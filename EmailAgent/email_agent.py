"""
Main Email Agent Orchestrator
Coordinates all components following the architecture diagram flow
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from config import Config
from models import (
    ProcessedEmail, ProcessingBatch, EmailMetadata,
    ProcessingStatus, EmailCategory
)

# Import all modules
from prompt.prompt_interpreter import PromptInterpreter
from tools import GmailClient, PermissionChecker
from core import (
    SenderClassifier, IntentDetector, PriorityScorer,
    EmailCategorizer, SpamFilter, ThreadSummarizer
)
from drafting import ReplyDrafter, TonePreserver, FollowUpGenerator
from edge_cases import ConflictResolver, LegalFinanceDetector, DNDHandler
from guardrails import PIIDetector, DomainChecker, ToneEnforcer
from output import QueueBuilder, MetricsGenerator
from logs.metrics_tracker import MetricsTracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailAgent:
    """
    Main Email Agent orchestrating the complete processing pipeline
    Following the architecture diagram flow
    """
    
    def __init__(self):
        logger.info("="*60)
        logger.info("Initializing Email Agent...")
        logger.info("="*60)
        self.prompt_interpreter = PromptInterpreter()
        self.action_plan = {}

        # S0: Start - Initialize all components
        self.gmail_client = None
        self.permission_checker = PermissionChecker()
        
        # Core processing modules
        self.classifier = SenderClassifier()
        self.intent_detector = IntentDetector()
        self.priority_scorer = PriorityScorer()
        self.categorizer = EmailCategorizer()
        self.spam_filter = SpamFilter()
        self.thread_summarizer = ThreadSummarizer()
        
        # Drafting modules
        self.reply_drafter = ReplyDrafter()
        self.tone_preserver = TonePreserver()
        self.followup_generator = FollowUpGenerator()
        
        # Edge case handlers
        self.conflict_resolver = ConflictResolver()
        self.legal_detector = LegalFinanceDetector()
        self.dnd_handler = DNDHandler()
        
        # Guardrails
        self.pii_detector = PIIDetector()
        self.domain_checker = DomainChecker()
        self.tone_enforcer = ToneEnforcer()
        
        # Output generators
        self.queue_builder = QueueBuilder()
        self.metrics_generator = MetricsGenerator()
        
        # Metrics tracking
        self.metrics_tracker = MetricsTracker()
        
        # Operating context
        self.operating_context = {}
        
        logger.info("✓ Email Agent initialized successfully")
    
    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Main execution flow following the architecture diagram
        
        Args:
            user_command: Natural language command from user
            user_scope: Optional scope parameters (time range, filters, etc.)
        
        Returns:
            Final response queue with metrics
        """

        logger.info("="*60)
        logger.info(f"STARTING EMAIL AGENT")
        logger.info(f"Command: {user_prompt}")
        logger.info("="*60)
        
        # S0: Interpret user prompt
        plan = self.prompt_interpreter.interpret(user_prompt)
        print(plan)
        # return
        # exit()
        
        # 🔥 COMPOSE SHORT-CIRCUIT
        if plan.get("intent") == "compose" or self.action_plan.get("compose_new"):
            compose = plan.get("compose") or {}
            to = compose.get("to")
            subject = compose.get("subject", "Request")
            body_intent = compose.get("body_intent", "")

            if not to:
                logger.error("Compose intent detected but recipient missing")
                return {"error": "Recipient email missing"}

            logger.info(f"Composing new email to {to}")

            draft = self.compose_new_email(
                recipients=to,   # ✅ already a list
                subject=subject,
                intent=body_intent,
                cc=compose.get("cc", []),
                bcc=compose.get("bcc", [])
            )
            if not draft:
                logger.error("Failed to generate draft")
                return {
                    "status": "error",
                    "error": "Draft generation failed",
                    "emails": [],
                    "metrics": {
                        "total_emails": 0,
                        "drafts_created": 0,
                        "high_priority": 0,
                        "medium_priority": 0,
                        "low_priority": 0,
                        "blocked_count": 0,
                        "vip_count": 0,
                        "time_saved_minutes": 0,
                        "categories": {}
                    }
                }

            # 📧 Show draft — nicely formatted (include CC and BCC)
            print("\n📧 Draft Email:")
            print("-" * 40)

            # recipients: can be list or single
            to_str = ", ".join(draft.recipients) if isinstance(draft.recipients, (list, tuple)) else str(draft.recipients)
            print(f"To: {to_str}")

            # cc / bcc may or may not exist on the DraftReply dataclass/object
            cc_list = getattr(draft, "cc", []) or []
            bcc_list = getattr(draft, "bcc", []) or []

            if cc_list:
                print(f"Cc: {', '.join(cc_list)}")
            if bcc_list:
                print(f"Bcc: {', '.join(bcc_list)}")

            print(f"Subject: {draft.subject}\n")
            print(draft.body)
            print("-" * 40)

            # ✅ Return draft for GUI to handle
            logger.info("Draft created successfully - returning to GUI")
            return {
                "status": "draft_created",
                "draft_id": draft.draft_id,
                "emails": [],
                "metrics": {
                    "total_emails": 0,
                    "drafts_created": 1,
                    "high_priority": 0,
                    "medium_priority": 0,
                    "low_priority": 0,
                    "blocked_count": 0,
                    "vip_count": 0,
                    "time_saved_minutes": 2,
                    "categories": {}
                },
                "draft": {
                    "to": to_str,
                    "cc": cc_list,
                    "bcc": bcc_list,
                    "subject": draft.subject,
                    "body": draft.body,
                    "draft_id": draft.draft_id
                }
            }

        
        
        user_scope = plan.get("scope", {})
        self.action_plan = plan.get("actions", {})

        logger.info(f"Derived scope: {user_scope}")
        logger.info(f"Derived actions: {self.action_plan}")

        # Determine if user explicitly asked for replies (force override)
        self.force_reply = False
        try:
            intent = plan.get("intent")
            actions = plan.get("actions", {})
            self.force_reply = (intent == "reply") and bool(actions.get("draft_replies", False))
        except Exception:
            self.force_reply = False


        # S1: User Command
        batch_id = str(uuid.uuid4())[:8]
        batch = ProcessingBatch(
            batch_id=batch_id,
            user_command=user_prompt,
            user_scope=user_scope or {}
        )
        
        # S2: User Scope Note
        logger.info(f"Batch ID: {batch_id}")
        logger.info(f"Scope: {user_scope}")
        
        try:
            # SECTION 1: Tool Permissions Check
            self.check_tool_permissions()
            
            # SECTION 2: Data Ingestion
            raw_emails = self.data_ingestion(user_scope)
            
            if not raw_emails:
                logger.warning("No emails found to process")
                return self.build_empty_response(batch)
            
            # Convert to ProcessedEmail objects
            emails = [self.create_processed_email(metadata) for metadata in raw_emails]
            batch.emails = emails
            
            logger.info(f"Processing {len(emails)} email(s)...")
            target = plan.get("target", {})
            sender_email = target.get("sender_email")

            if sender_email:
                batch.emails = [
                    e for e in batch.emails
                    if sender_email.lower() in e.metadata.sender.lower()
                ]

                if not batch.emails:
                    logger.warning(f"No emails found from {sender_email}")
                    return self.build_empty_response(batch)

                if target.get("latest_only"):
                    batch.emails = sorted(
                        batch.emails,
                        key=lambda e: e.metadata.date,
                        reverse=True
                    )[:1]

            # SECTION 3: Core Classification Pipeline
            for email in emails:
                self.process_email_core_pipeline(email)
            
            # SECTION 4: Edge Case Handling (parallel with core)
            self.handle_edge_cases(batch)
            
            # SECTION 5: Drafting
            for email in batch.emails:
                if not email.is_blocked:
                    self.draft_replies(email)
            
            # SECTION 6: Guardrails (Security checks)
            for email in batch.emails:
                self.apply_guardrails(email)
            
            # SECTION 7: Final Output
            batch.completed_at = datetime.now()
            batch.total_processed = len(batch.emails)
            
            response = self.generate_final_output(batch)
            
            logger.info("="*60)
            logger.info("✓ EMAIL AGENT COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in email agent: {e}", exc_info=True)
            batch.errors.append(str(e))
            return self.build_error_response(batch, str(e))
    
    def check_tool_permissions(self):
        """T1-T6: Tool Scopes and Permissions Check"""
        logger.info("\n" + "="*60)
        logger.info("SECTION 1: Checking Tool Permissions")
        logger.info("="*60)
        
        # Initialize Gmail client
        self.gmail_client = GmailClient()
        
        # T1-T2: Check Required Tool Scopes
        has_permissions, missing_scopes = self.permission_checker.check_required_tool_scopes(
            self.gmail_client.service
        )
        
        if not has_permissions:
            # T3: Set Entry Note
            note = self.permission_checker.set_entry_note(missing_scopes)
            logger.warning(note)
            
            # T4: Notify Missing Tool Scopes
            notification = self.permission_checker.notify_missing_tool_scopes(missing_scopes)
            logger.warning(f"Missing scopes: {notification}")
        
        # T5: Create Missing Context
        self.operating_context = self.permission_checker.create_missing_context(
            self.permission_checker.available_scopes
        )
        
        logger.info(f"Operating mode: {self.operating_context['mode']}")
    
    def data_ingestion(self, user_scope: Optional[Dict[str, Any]]) -> List[EmailMetadata]:
        """D1-D5: Data Ingestion Workflow"""
        logger.info("\n" + "="*60)
        logger.info("SECTION 2: Data Ingestion")
        logger.info("="*60)
        
        # Parse user scope
        query = user_scope.get('query', '') if user_scope else ''
        max_results = user_scope.get('max_results', Config.MAX_EMAILS_TO_PROCESS) if user_scope else Config.MAX_EMAILS_TO_PROCESS
        time_range = user_scope.get('time_range_days', 7) if user_scope else 7
        
        # D1: Fetch Emails
        messages = self.gmail_client.fetch_emails(
            query=query,
            max_results=max_results,
            time_range_days=time_range
        )
        
        # D2: Inbox Scan + D4: Metadata Extraction
        email_metadata_list = []
        for msg in messages:
            email_details = self.gmail_client.get_email_details(msg['id'])
            if email_details:
                metadata = self.gmail_client.extract_metadata(email_details)
                email_metadata_list.append(metadata)
        
        # D3: Thread Mapping
        message_ids = [msg['id'] for msg in messages]
        thread_map = self.gmail_client.get_threads(message_ids)
        logger.info(f"Mapped into {len(thread_map)} thread(s)")
        
        # D5: Start Mode Note
        logger.info("✓ Data ingestion complete")
        
        return email_metadata_list
    
    def create_processed_email(self, metadata: EmailMetadata) -> ProcessedEmail:
        """Create ProcessedEmail object from metadata"""
        return ProcessedEmail(
            metadata=metadata,
            status=ProcessingStatus.PENDING,
            received_at=metadata.date
        )
    
    def process_email_core_pipeline(self, email: ProcessedEmail):
        """S1-S16: Core Classification Pipeline"""
        email.status = ProcessingStatus.PROCESSING
        if not hasattr(email, "processing_notes"):
            email.processing_notes = []

        # S1: Sender Classification
        email.classification = self.classifier.classify(email.metadata)
        # --- Explanation: classification notes ---
        if not hasattr(email, "processing_notes"):
            email.processing_notes = []

        # Append classifier notes if present
        if getattr(email.classification, "notes", None):
            email.processing_notes.append(f"Classification notes: {email.classification.notes}")

        # Append sender type / VIP
        try:
            email.processing_notes.append(
                f"Sender type: {email.classification.sender_type.value}, VIP: {bool(email.classification.is_vip)}"
            )
        except Exception:
            # defensive: some test objects may not have fields
            pass

        # S2: Keyword and Intent Detection
        email.intent = self.intent_detector.detect(email.metadata)
        # --- Explanation: intent notes ---
        if getattr(email, "intent", None):
            if getattr(email.intent, "primary_intent", None):
                email.processing_notes.append(f"Intent detected: {email.intent.primary_intent}")
            # detected keywords
            kws = getattr(email.intent, "keywords_detected", None)
            if kws:
                try:
                    email.processing_notes.append(f"Keywords: {', '.join(kws)}")
                except Exception:
                    email.processing_notes.append(f"Keywords: {kws}")
            # urgency keywords
            urgency_kws = getattr(email.intent, "urgency_keywords", None)
            if urgency_kws:
                try:
                    email.processing_notes.append(f"Urgency keywords: {', '.join(urgency_kws)}")
                except Exception:
                    email.processing_notes.append(f"Urgency keywords: {urgency_kws}")

        # S3: Priority Scoring Engine
        email.priority = self.priority_scorer.calculate_score(
            email.metadata,
            email.classification,
            email.intent
        )
        # --- Explanation: priority notes ---
        
        if self.action_plan.get("only_urgent"):
            if email.priority.priority_level.name != "HIGH":
                email.is_blocked = True
                email.status = ProcessingStatus.SKIPPED
                email.processing_notes.append("Skipped (only urgent requested)")
                return

        if getattr(email, "priority", None):
            try:
                score = email.priority.score
            except Exception:
                score = getattr(email.priority, "score", None) or 0
            level = getattr(email.priority, "priority_level", None)
            if level:
                level_name = level.name if hasattr(level, "name") else str(level)
            else:
                level_name = "UNKNOWN"
            email.processing_notes.append(f"Priority score: {score}/100 ({level_name})")
            if getattr(email.priority, "reasoning", None):
                email.processing_notes.append(f"Priority reasoning: {email.priority.reasoning}")

        # S4: High Priority Decision + S5: Map to Important / Mark as NotReq
        # (handled automatically by priority_scorer)
        
        # S3.5: Thread Summarization (PRD Step 3)
        try:
            email.thread_summary = self.thread_summarizer.summarize_single_email(email.metadata)
            if email.thread_summary and email.thread_summary.get('summary'):
                email.processing_notes.append(f"Thread summary: {email.thread_summary['summary'][:100]}")
                if email.thread_summary.get('open_questions'):
                    email.processing_notes.append(f"Open questions: {len(email.thread_summary['open_questions'])}")
        except Exception as e:
            logger.error(f"Thread summarization failed: {e}")
            email.thread_summary = None
        
        # S6-S7: Categorization
        email.is_spam = self.spam_filter.is_spam(email.metadata, email.classification)
        email.category = self.categorizer.categorize(
            email.intent,
            email.priority,
            email.is_spam
        )
        # --- Explanation: category & spam notes ---
        try:
            email.processing_notes.append(f"Category assigned: {email.category.value}")
        except Exception:
            email.processing_notes.append(f"Category assigned: {email.category}")

        if email.is_spam:
            email.processing_notes.append("Marked as SPAM by spam filter")
            # email.is_blocked already set later; leave that logic unchanged

        # S8-S9: Spam Check
        if email.is_spam:
            self.spam_filter.mark_as_blocked(email.metadata.message_id)
            email.is_blocked = True
            email.status = ProcessingStatus.BLOCKED
            return
        
        # S11: Draft Reply Decision
        email.requires_reply = (
            email.intent.action_required or
            email.intent.question_detected or
            email.category in [EmailCategory.ACTION]
        )
        # --- Explanation: reply requirement ---
        if email.requires_reply:
            email.processing_notes.append("Marked as requiring a reply")
        else:
            email.processing_notes.append("No reply required")

    def handle_edge_cases(self, batch: ProcessingBatch):
        """E1-E9: Edge Case Handling"""
        logger.info("\n" + "="*60)
        logger.info("SECTION 3: Edge Case Handling")
        logger.info("="*60)

        # E1-E2: Multiple emails from same sender (resolve + explain)
        conflicts = self.conflict_resolver.check_multiple_from_same_sender(batch.emails)
        if conflicts:
            active_emails = self.conflict_resolver.resolve_conflicts(conflicts)

            # Build a set of active message ids
            active_ids = {e.metadata.message_id for e in active_emails}

            # Mark emails not in active_ids as superseded and append notes
            for e in batch.emails:
                if e.metadata.message_id not in active_ids:
                    # do not change blocking / core logic; only add explanation
                    if not hasattr(e, "processing_notes"):
                        e.processing_notes = []
                    e.processing_notes.append("Superseded by a newer email from the same sender")

            # Rebuild batch.emails: preserve emails from senders that had no conflict, plus the chosen active emails
            non_conflict_emails = [e for e in batch.emails if e.metadata.sender not in conflicts]
            batch.emails = non_conflict_emails + active_emails
            logger.info(f"Resolved sender conflicts; active emails count: {len(batch.emails)}")

        
        # E3-E4: Legal/Finance Detection
        for email in batch.emails:
            if not email.is_blocked:
                is_critical = self.legal_detector.check_legal_finance_content_urgent(email)
                if is_critical:
                    self.legal_detector.block_auto_reply_and_escalate(email)
        
        # E5-E9: DND Mode and Tool Alerts
        can_send = self.operating_context.get('can_send', False)
        
        for email in batch.emails:
            if not email.is_blocked:
                # E5-E6: Tool Alert
                has_alert, alert_reason = self.dnd_handler.check_tool_alert(can_send)
                if has_alert:
                    self.dnd_handler.force_draft_only_and_warn(email, alert_reason)
                
                # E7-E9: DND Mode
                if self.dnd_handler.check_external_email_to_dnd(email):
                    dnd_decision = self.dnd_handler.handle_dnd_decision(email)
                    logger.info(f"DND decision: {dnd_decision}")
    
    def draft_replies(self, email: ProcessedEmail):
        """S11-S15: Drafting Pipeline"""

        if (not email.requires_reply and self.force_reply is False) or email.is_blocked:
            return

        if not self.action_plan.get("draft_replies", False):
            return

        # S12: Draft Reply (Gemini → template)
        draft = self.reply_drafter.draft_reply(
            email.metadata,
            email.intent
        )

        if not draft:
            return

        email.draft_reply = draft

        # 🔹 SAVE DRAFT TO GMAIL
        try:
            # Take recipients/cc/bcc/subject/body from the DraftReply object
            recipients = draft.recipients if isinstance(draft.recipients, (list, tuple)) else [draft.recipients]
            cc = getattr(draft, "cc", []) or []
            bcc = getattr(draft, "bcc", []) or []
            subject = draft.subject
            body = draft.body

            # Defensive normalization (flatten lists)
            def _norm_list(x):
                if not x:
                    return []
                if isinstance(x, str):
                    return [s.strip() for s in x.split(",") if s.strip()]
                flat = []
                for item in x:
                    if isinstance(item, (list, tuple)):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return flat

            recipients = _norm_list(recipients)
            cc = _norm_list(cc)
            bcc = _norm_list(bcc)

            draft_id = self.gmail_client.create_draft(
                to=recipients,
                cc=cc,
                bcc=bcc,
                subject=subject,
                body=body
            )

            if draft_id:
                draft.draft_id = draft_id
                logger.info(f"✓ Draft saved to Gmail (draft_id={draft_id})")
            else:
                logger.warning("Draft generated but Gmail returned no draft id")

        except Exception as e:
            logger.error(f"Failed to save Gmail draft: {e}")
            return


        # --------------------------------------------------
        # 🧠 HUMAN CONFIRMATION (THIS IS WHERE IT GOES)
        # --------------------------------------------------
        if email.draft_reply.requires_approval:
            print("\n📧 Draft Reply:")
            print("-" * 40)
            print(email.draft_reply.body)
            print("-" * 40)

            confirm = input("Send this email? (yes/no): ").strip().lower()

            if confirm != "yes":
                email.processing_notes.append("User declined to send draft")
                logger.info("User declined to send the draft")
                return

            logger.info("User approved draft for sending")

            # ⚠️ NOTE: actual send logic can go here later

        # S14: Tone and Timing Check
        should_delay = self.tone_preserver.preserves_tone_or_reply_after_hour(draft)

        # S15: Follow-ups
        if should_delay and self.action_plan.get("include_followups"):
            email.follow_ups = self.followup_generator.generate_follow_ups(
                email.metadata,
                email.intent
            )

    
    def apply_guardrails(self, email: ProcessedEmail):
        """G1-G7: Guardrails and Security"""
        logger.debug(f"Applying guardrails to: {email.metadata.subject}")
        
        # G1: PII Detection
        has_pii, pii_types = self.pii_detector.detect_pii_and_confidential(email)
        # --- Explanation: PII detection notes ---
        if self.action_plan.get("require_approval") and email.draft_reply:
            email.draft_reply.requires_approval = True

        if has_pii:
            email.has_pii = True
            if not hasattr(email, "processing_notes"):
                email.processing_notes = []
            if pii_types:
                email.processing_notes.append(f"PII detected: {', '.join(pii_types)}")
            else:
                email.processing_notes.append("PII detected (types not identified)")

        # G2: Domain Restriction Check
        domain_approved = self.domain_checker.check_domain_restrictions(email)
        # --- Explanation: domain restriction notes ---
        if not domain_approved:
            if not hasattr(email, "processing_notes"):
                email.processing_notes = []
            email.processing_notes.append("Domain restriction: external domain not approved for automatic action")

        # G3: Safe Tone Enforcement
        if email.draft_reply:
            tone_approved, tone_issues = self.tone_enforcer.enforce_safe_tone(email)
        else:
            tone_approved = True
        # --- Explanation: tone enforcement notes ---
        if not tone_approved:
            if not hasattr(email, "processing_notes"):
                email.processing_notes = []
            if tone_issues:
                email.processing_notes.append(f"Tone issues found: {', '.join(tone_issues)}")
            else:
                email.processing_notes.append("Tone enforcement flagged the draft")

        # G4: External Email or High Risk?
        is_external = self.domain_checker.is_external_email(email)
        has_security_flags = len(email.security_flags) > 0
        
        if is_external or has_security_flags:
            # G5: Approval Required
            email.status = ProcessingStatus.APPROVAL_REQUIRED
            if email.draft_reply:
                email.draft_reply.requires_approval = True
            logger.info(f"⚠️ Approval required for: {email.metadata.subject}")
            email.processing_notes.append("Approval required due to external sender or high-risk security flags")
        else:
            # G6: Draft Marked Ready
            email.status = ProcessingStatus.DRAFT_READY
            if email.draft_reply:
                email.draft_reply.requires_approval = False  # Can auto-send if configured
        
        # G7: Guardrail Rules Note (logged)
        logger.debug("Guardrails applied successfully")

    def generate_final_output(self, batch: ProcessingBatch) -> Dict[str, Any]:
        """F1-F2: Final Output Generation"""
        logger.info("\n" + "="*60)
        logger.info("SECTION 4: Generating Final Output")
        logger.info("="*60)
        
        # F1: Build Final Response Queue
        queue = self.queue_builder.build_final_queue(batch)
        
        # F2: Generate Metrics Panel
        metrics = self.metrics_generator.generate_metrics(batch)
        metrics_display = self.metrics_generator.format_metrics_display(metrics)
        
        print("\n" + metrics_display)
        
        print("\nTOP 10 IMPORTANT EMAILS (with reasons):")
        print(json.dumps(queue.get("top_10_emails", []), indent=2, default=str))

        # Combine into final response
        response = {
            "queue": queue,
            "metrics": metrics,
            "batch_info": {
                "batch_id": batch.batch_id,
                "started_at": batch.started_at.isoformat(),
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                "command": batch.user_command
            }
        }
        
        return response
    
    def build_empty_response(self, batch: ProcessingBatch) -> Dict[str, Any]:
        """Build response when no emails found"""
        return {
            "queue": {
                "batch_id": batch.batch_id,
                "summary": {"total_processed": 0},
                "message": "No emails found matching criteria"
            },
            "metrics": None
        }
    
    def build_error_response(self, batch: ProcessingBatch, error: str) -> Dict[str, Any]:
        """Build error response"""
        return {
            "error": error,
            "batch_id": batch.batch_id,
            "errors": batch.errors
        }

    def compose_new_email(
        self,
        recipients: list,
        subject: str,
        intent: str,
        cc: list | None = None,
        bcc: list | None = None
    ):
        """Compose and create a new draft email"""
        if not recipients:
            return None
        
        # Ensure client is initialized
        if not self.gmail_client:
            from tools import GmailClient
            self.gmail_client = GmailClient()
        
        logger.info(f"Composing new email to {recipients} with intent: {intent}")
        
        # Use Gemini AI to generate email body
        body = None
        try:
            from google import genai
            gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
            
            prompt = f"""Write a professional, concise email.

Recipient: {recipients[0] if recipients else 'recipient'}
Subject: {subject}
Purpose: {intent}

Rules:
- Write ONLY the email body (no subject line)
- Be professional and friendly
- Keep it concise (3-5 sentences)
- End with a polite closing
- Do not use placeholders like [Your Name]
"""
            
            response = gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt
            )
            
            if hasattr(response, "text") and response.text:
                body = response.text.strip()
                logger.info("✓ Email body generated with Gemini AI")
            else:
                body = None
        except Exception as e:
            logger.warning(f"Gemini compose failed: {e}")
            body = None
        
        # Fallback body if AI fails
        if not body:
            logger.info("Using fallback email template")
            # Create a more natural fallback based on intent
            if intent:
                body = f"""Hi,

{intent}

Looking forward to your response.

Best regards"""
            else:
                body = """Hi,

I wanted to reach out to you.

Looking forward to hearing from you.

Best regards"""

        # Sanitize LLM output: remove any leading "Subject:" line(s)
        import re
        body = re.sub(r'(?mi)^\s*Subject:.*\n', '', body).strip()

        # Defensive normalization — ensure lists
        def _norm_list(x):
            if not x:
                return []
            if isinstance(x, str):
                return [s.strip() for s in x.split(",") if s.strip()]
            if isinstance(x, (list, tuple)):
                flat = []
                for item in x:
                    if isinstance(item, (list, tuple)):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return [s for s in flat if s]
            return [str(x)]

        cc = _norm_list(cc)
        bcc = _norm_list(bcc)
        recipients = _norm_list(recipients)

        # Create draft in Gmail
        try:
            draft_id = self.gmail_client.create_draft(
                to=recipients,
                cc=cc,
                bcc=bcc,
                subject=subject,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to create Gmail draft: {e}")
            draft_id = None
        
        if draft_id:
            from models import DraftReply
            draft = DraftReply(
                draft_id=draft_id,
                subject=subject,
                body=body,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                requires_approval=True
            )
            logger.info(f"✓ Draft created successfully (draft_id={draft_id})")
            return draft
        else:
            # Even if draft creation fails, return a DraftReply object
            # so the GUI can display it (just without a draft_id)
            from models import DraftReply
            logger.warning("Draft creation failed, returning draft object without Gmail draft_id")
            draft = DraftReply(
                draft_id="local_draft",
                subject=subject,
                body=body,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                requires_approval=True
            )
            return draft

    def send_draft(self, draft_id: str) -> bool:
        """Send a draft by ID"""
        logger.info("="*60)
        logger.info("📤 EMAIL_AGENT.send_draft() called")
        logger.info(f"   Draft ID: {draft_id}")
        logger.info(f"   Draft ID type: {type(draft_id)}")
        logger.info(f"   Gmail client exists: {self.gmail_client is not None}")
        
        if not self.gmail_client:
            logger.info("   Creating new Gmail client...")
            from tools import GmailClient
            self.gmail_client = GmailClient()
            logger.info("   ✓ Gmail client created")
        
        logger.info(f"   Calling gmail_client.send_email(draft_id='{draft_id}')...")
        try:
            result = self.gmail_client.send_email(draft_id=draft_id)
            logger.info(f"   Gmail API returned: {result} (type: {type(result)})")
            
            if result:
                logger.info(f"✅ Successfully sent draft {draft_id}")
                logger.info("="*60)
            else:
                logger.error(f"❌ Failed to send draft {draft_id}")
                logger.error("   Gmail API returned False/None")
                logger.info("="*60)
            return result
        except Exception as e:
            logger.error(f"❌ Exception in send_draft: {e}")
            logger.error(f"   Exception type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info("="*60)
            return False


# Main entry point
def main():
    """Main entry point for Email Agent"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║              📧 EMAIL AGENT v1.0 📧                   ║
    ║                                                       ║
    ║         AI-Powered Email Management System            ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Validate configuration
    missing = Config.validate()
    if missing:
        logger.error(f"❌ Missing configuration: {', '.join(missing)}")
        logger.error("Please update your .env file with required values")
        return
    
    # Create agent
    agent = EmailAgent()
    
    # Example user command
    # user_command = "Handle my inbox from today. Show only urgent items. Draft replies for approval and create follow-ups."
    user_scope = {
        'time_range_days': 1,
        'max_results': 50
    }
    user_prompt = input("\n🧠 What would you like me to do with your inbox?\n> ")
    # user_command= user_prompt
    result = agent.run(user_prompt)

    # Run agent
    # result = agent.run(user_command, user_scope)
    
    # Display results
    if "error" in result:
        logger.error(f"❌ Agent failed: {result['error']}")
    else:
        logger.info("\n✓ Processing complete!")
        if isinstance(result, dict) and "batch_info" in result:
            logger.info(f"See batch {result['batch_info']['batch_id']} for results")
        elif isinstance(result, dict) and result.get("status") == "draft_created":
            logger.info(f"Draft created successfully (draft_id={result.get('draft_id')})")
        else:
            logger.info("Operation completed (no batch generated)")


if __name__ == "__main__":
    main()
