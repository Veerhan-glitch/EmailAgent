"""
S12: Draft Reply
Generates draft email replies using Gemini with Ollama fallback
(FIXED: user-provided reply intent is now respected)
"""

import logging
from typing import Optional
from datetime import datetime

from LLM.llm_adapter import LLMAdapter
from config import Config
from models import DraftReply, EmailMetadata, IntentDetection

# Gemini SDK (optional)
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


class ReplyDrafter:
    """Generates draft email replies"""

    def __init__(self):
        self.use_gemini = Config.GEMINI_ENABLED and bool(Config.GEMINI_API_KEY) and genai is not None
        self.ollama = LLMAdapter(model="llama3.1:8b")

        self.gemini_client = None
        if self.use_gemini:
            try:
                self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.use_gemini = False

    # --------------------------------------------------------------
    # MAIN ENTRY
    # --------------------------------------------------------------

    def draft_reply(
        self,
        metadata: EmailMetadata,
        intent: IntentDetection
    ) -> Optional[DraftReply]:

        logger.info(f"Drafting reply for: {metadata.subject}")

        draft_body: Optional[str] = None

        # 🔹 Extract user-provided reply content (CRITICAL FIX)
        user_reply_text = getattr(intent, "user_supplied_text", None)

        # 1️⃣ Build prompt
        context = self._build_context(metadata, intent, user_reply_text)

        # 2️⃣ Try Gemini (optional)
        # if self.use_gemini:
        #     try:
        #         draft_body = self._generate_with_gemini(context)
        #     except Exception as e:
        #         logger.error(f"Gemini failed: {e}")
        #         draft_body = None

        # 3️⃣ Ollama fallback
        if not draft_body:
            logger.warning("Falling back to Ollama for reply drafting")
            draft_body = self.ollama.generate_with_ollama(context)

        # 4️⃣ Template fallback (guaranteed)
        if not draft_body:
            logger.info("Using fallback template for draft reply")
            draft_body = self._generate_template_response(metadata, intent)

        if not draft_body:
            logger.error("Draft generation failed completely")
            return None

        subject = self._create_reply_subject(metadata.subject)
        
        # Detect reply-all risk (PRD requirement)
        total_recipients = len(metadata.recipients) + len(metadata.cc)
        external_count = self._count_external_recipients(metadata)
        reply_all_risk = self._detect_reply_all_risk(metadata)
        
        # Generate evidence
        evidence = [
            f"Original sender: {metadata.sender}",
            f"Total recipients: {total_recipients}",
            f"External recipients: {external_count}"
        ]
        if reply_all_risk:
            evidence.append("⚠️ Large reply-all detected - requires approval")
        
        # Generate reasoning
        reasoning = "AI-generated reply based on email context and intent"
        if user_reply_text:
            reasoning += " (user-provided content incorporated)"
        
        draft = DraftReply(
            subject=subject,
            body=draft_body.strip(),
            recipients=[metadata.sender],
            cc=[],
            tone="professional",
            preserves_tone=True,
            created_at=datetime.now(),
            requires_approval=True,
            reasoning=reasoning,
            confidence=0.85,
            evidence=evidence,
            external_recipients=external_count,
            reply_all_risk=reply_all_risk
        )

        logger.info("✓ Draft reply generated")
        return draft

    # --------------------------------------------------------------
    # GEMINI (OPTIONAL)
    # --------------------------------------------------------------

    def _generate_with_gemini(self, context: str) -> Optional[str]:
        if not self.gemini_client:
            return None

        try:
            response = self.gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=context
            )

            if hasattr(response, "text") and response.text:
                return response.text.strip()

            try:
                return response.output[0].content[0].text.strip()
            except Exception:
                return None

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    # --------------------------------------------------------------
    # PROMPT BUILDER (FIXED)
    # --------------------------------------------------------------

    def _build_context(
        self,
        metadata: EmailMetadata,
        intent: IntentDetection,
        user_reply_text: Optional[str]
    ) -> str:
        """
        If user supplied reply content, LLM is ONLY allowed
        to rephrase it politely — not invent content.
        """

        if user_reply_text:
            return (
                "Rewrite the following reply in a polite, professional tone.\n\n"
                f"Original subject: {metadata.subject}\n"
                f"Sender: {metadata.sender}\n\n"
                "User reply content (DO NOT CHANGE MEANING):\n"
                f"\"{user_reply_text}\"\n\n"
                "Rules:\n"
                "- Do NOT add new information\n"
                "- Do NOT acknowledge or summarize the email\n"
                "- Do NOT promise actions\n"
                "- Keep it concise (1–2 sentences)\n"
                "- No placeholders\n\n"
                "Final reply:"
            )

        # Default behavior (no user text provided)
        return (
            "Write a short, polite, professional email reply.\n\n"
            f"Original subject: {metadata.subject}\n"
            f"Sender: {metadata.sender}\n"
            f"Intent: {intent.primary_intent}\n\n"
            "Rules:\n"
            "- Be polite and professional\n"
            "- Acknowledge the email\n"
            "- Do not promise actions\n"
            "- Keep it to 2–3 sentences\n\n"
            "Draft reply:"
        )
    
    def _count_external_recipients(self, metadata: EmailMetadata) -> int:
        """Count external email recipients (outside organization domain)"""
        external_count = 0
        all_emails = metadata.recipients + metadata.cc + metadata.bcc
        
        for email in all_emails:
            # Check if email domain is external (simplified check)
            if '@' in email:
                domain = email.split('@')[1]
                # Could check against Config.ALLOWED_DOMAINS if available
                if not any(domain.endswith(allowed) for allowed in getattr(Config, 'ALLOWED_DOMAINS', [])):
                    external_count += 1
        
        return external_count
    
    def _detect_reply_all_risk(self, metadata: EmailMetadata) -> bool:
        """
        Detect reply-all risk: large number of external recipients (PRD requirement)
        """
        total_recipients = len(metadata.recipients) + len(metadata.cc)
        external_count = self._count_external_recipients(metadata)
        
        # Risk if >5 total recipients OR >2 external recipients
        if total_recipients > 5:
            logger.warning(f"Reply-all risk: {total_recipients} total recipients")
            return True
        
        if external_count > 2:
            logger.warning(f"Reply-all risk: {external_count} external recipients")
            return True
        
        return False

    # --------------------------------------------------------------
    # TEMPLATE FALLBACK
    # --------------------------------------------------------------

    def _generate_template_response(
        self,
        metadata: EmailMetadata,
        intent: IntentDetection
    ) -> str:

        templates = {
            "question": (
                "Thank you for your email. I’ve received your question and will "
                "review it shortly.\n\nBest regards"
            ),
            "request": (
                "Thank you for reaching out. I’ve noted your request and will "
                "follow up soon.\n\nBest regards"
            ),
            "default": (
                "Thank you for your email. I’ve received your message and will "
                "respond accordingly.\n\nBest regards"
            ),
        }

        key = intent.primary_intent if intent.primary_intent in templates else "default"
        return templates[key]

    # --------------------------------------------------------------
    # SUBJECT HELPER
    # --------------------------------------------------------------

    def _create_reply_subject(self, original_subject: str) -> str:
        if original_subject.lower().startswith("re:"):
            return original_subject
        return f"Re: {original_subject}"
