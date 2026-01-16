"""
Email Agent Feature Verification Test Script
Tests all PRD requirements to ensure proper implementation
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from models import (
    EmailMetadata, ProcessedEmail, ClassificationResult,
    IntentDetection, PriorityScore, DraftReply, SecurityFlag,
    SenderType, PriorityLevel, ProcessingStatus
)

# Import all modules
from core import (
    SenderClassifier, IntentDetector, PriorityScorer,
    EmailCategorizer, SpamFilter, ThreadSummarizer
)
from drafting import ReplyDrafter, TonePreserver, FollowUpGenerator
from edge_cases import ConflictResolver, LegalFinanceDetector, DNDHandler
from guardrails import PIIDetector, DomainChecker, ToneEnforcer
from output import QueueBuilder, MetricsGenerator
from logs.metrics_tracker import MetricsTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureVerifier:
    """Verifies all PRD features are working correctly"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, condition: bool, details: str = ""):
        """Test a single feature"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results.append({
            'name': name,
            'status': status,
            'condition': condition,
            'details': details
        })
        
        if condition:
            self.passed += 1
            logger.info(f"{status}: {name}")
        else:
            self.failed += 1
            logger.error(f"{status}: {name} - {details}")
        
        return condition
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print("📊 EMAIL AGENT PRD VERIFICATION SUMMARY")
        print("="*70)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("="*70)
        
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['condition']:
                    print(f"  - {result['name']}: {result['details']}")
        
        print("\n")


def create_test_email(subject="Test Email", body="This is a test email.", 
                     sender="test@example.com", is_urgent=False) -> EmailMetadata:
    """Create test email metadata"""
    if is_urgent:
        body = "URGENT: This requires immediate attention. Deadline is today!"
    
    return EmailMetadata(
        message_id="test_123",
        thread_id="thread_123",
        subject=subject,
        sender=sender,
        sender_name="Test Sender",
        recipients=["user@company.com"],
        cc=[],
        bcc=[],
        date=datetime.now(),
        has_attachments=False,
        attachment_count=0,
        labels=[],
        snippet=body[:100],
        body_text=body,
        body_html=""
    )


def main():
    """Run all verification tests"""
    print("\n" + "="*70)
    print("🚀 STARTING EMAIL AGENT PRD VERIFICATION")
    print("="*70 + "\n")
    
    verifier = FeatureVerifier()
    
    # ============================================================
    # SECTION 1: Core Modules Initialization
    # ============================================================
    print("\n📦 SECTION 1: Core Modules Initialization")
    print("-" * 70)
    
    try:
        classifier = SenderClassifier()
        verifier.test("SenderClassifier initialization", True)
    except Exception as e:
        verifier.test("SenderClassifier initialization", False, str(e))
    
    try:
        intent_detector = IntentDetector()
        verifier.test("IntentDetector initialization", True)
    except Exception as e:
        verifier.test("IntentDetector initialization", False, str(e))
    
    try:
        priority_scorer = PriorityScorer()
        verifier.test("PriorityScorer initialization", True)
    except Exception as e:
        verifier.test("PriorityScorer initialization", False, str(e))
    
    try:
        categorizer = EmailCategorizer()
        verifier.test("EmailCategorizer initialization", True)
    except Exception as e:
        verifier.test("EmailCategorizer initialization", False, str(e))
    
    try:
        spam_filter = SpamFilter()
        verifier.test("SpamFilter initialization", True)
    except Exception as e:
        verifier.test("SpamFilter initialization", False, str(e))
    
    try:
        thread_summarizer = ThreadSummarizer()
        verifier.test("ThreadSummarizer initialization", True)
    except Exception as e:
        verifier.test("ThreadSummarizer initialization", False, str(e))
    
    try:
        reply_drafter = ReplyDrafter()
        verifier.test("ReplyDrafter initialization", True)
    except Exception as e:
        verifier.test("ReplyDrafter initialization", False, str(e))
    
    try:
        pii_detector = PIIDetector()
        verifier.test("PIIDetector initialization", True)
    except Exception as e:
        verifier.test("PIIDetector initialization", False, str(e))
    
    try:
        domain_checker = DomainChecker()
        verifier.test("DomainChecker initialization", True)
    except Exception as e:
        verifier.test("DomainChecker initialization", False, str(e))
    
    try:
        tone_enforcer = ToneEnforcer()
        verifier.test("ToneEnforcer initialization", True)
    except Exception as e:
        verifier.test("ToneEnforcer initialization", False, str(e))
    
    try:
        metrics_tracker = MetricsTracker()
        verifier.test("MetricsTracker initialization", True)
    except Exception as e:
        verifier.test("MetricsTracker initialization", False, str(e))
    
    # ============================================================
    # SECTION 2: Classification & Prioritization
    # ============================================================
    print("\n🔍 SECTION 2: Classification & Prioritization")
    print("-" * 70)
    
    # Test VIP detection
    vip_email = create_test_email(sender="ceo@company.com")
    classification = classifier.classify(vip_email)
    verifier.test(
        "VIP detection",
        classification.is_vip or classification.sender_type == SenderType.VIP,
        "VIP should be detected for CEO emails"
    )
    
    # Test intent detection
    question_email = create_test_email(
        subject="Quick question about the project",
        body="Can you please clarify the deadline? When is this due?"
    )
    intent = intent_detector.detect(question_email)
    verifier.test(
        "Question detection",
        intent.question_detected,
        "Should detect question marks and question words"
    )
    
    # Test urgency detection
    urgent_email = create_test_email(is_urgent=True)
    urgent_intent = intent_detector.detect(urgent_email)
    verifier.test(
        "Urgency keyword detection",
        len(urgent_intent.urgency_keywords) > 0,
        f"Found {len(urgent_intent.urgency_keywords)} urgency keywords"
    )
    
    # Test priority scoring
    urgent_classification = ClassificationResult(
        sender_type=SenderType.VIP,
        sender_email="ceo@company.com",
        sender_domain="company.com",
        is_vip=True,
        confidence=1.0
    )
    priority = priority_scorer.calculate_score(
        urgent_email, urgent_classification, urgent_intent
    )
    verifier.test(
        "Priority scoring (VIP + urgent)",
        priority.score >= 70,
        f"Score: {priority.score}/100"
    )
    
    # Test hidden urgency detection
    polite_urgent = create_test_email(
        subject="Quick request",
        body="Please kindly review this by end of day today. Thank you!"
    )
    polite_intent = intent_detector.detect(polite_urgent)
    polite_priority = priority_scorer.calculate_score(
        polite_urgent, classification, polite_intent
    )
    verifier.test(
        "Hidden urgency detection",
        polite_priority.hidden_urgency,
        "Polite language + deadline should trigger hidden urgency"
    )
    
    # ============================================================
    # SECTION 3: Thread Summarization
    # ============================================================
    print("\n📝 SECTION 3: Thread Summarization")
    print("-" * 70)
    
    # Test thread summarization
    test_email = create_test_email(
        subject="Project Update Meeting",
        body="We decided to move forward with option A. Question: What is the timeline? Action: John will follow up next week."
    )
    summary = thread_summarizer.summarize_single_email(test_email)
    
    verifier.test(
        "Thread summary generation",
        summary is not None and 'summary' in summary,
        f"Method: {summary.get('method', 'unknown')}"
    )
    
    verifier.test(
        "Summary structure completeness",
        all(key in summary for key in ['summary', 'key_points', 'decisions_made', 
                                        'open_questions', 'action_items', 'sentiment']),
        "All required keys present"
    )
    
    verifier.test(
        "Decision extraction",
        len(summary.get('decisions_made', [])) > 0 or summary.get('method') == 'rule_based',
        f"Found {len(summary.get('decisions_made', []))} decisions"
    )
    
    # ============================================================
    # SECTION 4: Drafting & Reply Generation
    # ============================================================
    print("\n✍️ SECTION 4: Drafting & Reply Generation")
    print("-" * 70)
    
    # Test draft generation
    draft = reply_drafter.draft_reply(test_email, polite_intent)
    
    verifier.test(
        "Draft reply generation",
        draft is not None,
        "Draft should be generated"
    )
    
    if draft:
        verifier.test(
            "Draft has subject",
            bool(draft.subject),
            f"Subject: {draft.subject[:50]}"
        )
        
        verifier.test(
            "Draft has body",
            len(draft.body) > 0,
            f"Length: {len(draft.body)} chars"
        )
        
        verifier.test(
            "Draft requires approval (default)",
            draft.requires_approval,
            "External emails should require approval"
        )
        
        verifier.test(
            "Draft includes reasoning",
            bool(draft.reasoning),
            draft.reasoning[:50]
        )
        
        verifier.test(
            "Draft includes confidence score",
            0.0 <= draft.confidence <= 1.0,
            f"Confidence: {draft.confidence}"
        )
        
        verifier.test(
            "Draft includes evidence",
            len(draft.evidence) > 0,
            f"{len(draft.evidence)} evidence items"
        )
        
        # Test reply-all risk detection
        many_recipients = create_test_email()
        many_recipients.recipients = ["user1@example.com", "user2@example.com", 
                                     "user3@example.com", "user4@example.com",
                                     "user5@example.com", "user6@example.com"]
        draft_many = reply_drafter.draft_reply(many_recipients, intent)
        
        if draft_many:
            verifier.test(
                "Reply-all risk detection",
                draft_many.reply_all_risk,
                f"{len(many_recipients.recipients)} recipients should trigger risk"
            )
    
    # ============================================================
    # SECTION 5: Guardrails & Safety
    # ============================================================
    print("\n🛡️ SECTION 5: Guardrails & Safety")
    print("-" * 70)
    
    # Test PII detection
    pii_email = ProcessedEmail(
        metadata=create_test_email(
            body="My SSN is 123-45-6789 and credit card is 4111-1111-1111-1111"
        )
    )
    has_pii, pii_types = pii_detector.detect_pii_and_confidential(pii_email)
    
    verifier.test(
        "PII detection (SSN)",
        'ssn' in pii_types,
        f"Detected: {pii_types}"
    )
    
    verifier.test(
        "PII detection (credit card)",
        'credit_card' in pii_types,
        f"Detected: {pii_types}"
    )
    
    verifier.test(
        "PII blocks sending",
        len(pii_email.security_flags) > 0 and pii_email.security_flags[0].blocks_sending,
        "PII should block sending"
    )
    
    # Test tone enforcement
    aggressive_email = ProcessedEmail(
        metadata=create_test_email(),
        draft_reply=DraftReply(
            subject="Re: Test",
            body="You MUST do this IMMEDIATELY or else! We GUARANTEE this will work.",
            recipients=["user@example.com"]
        )
    )
    tone_ok, tone_issues = tone_enforcer.enforce_safe_tone(aggressive_email)
    
    verifier.test(
        "Aggressive tone detection",
        not tone_ok and len(tone_issues) > 0,
        f"Detected {len(tone_issues)} tone issues"
    )
    
    # Test legal/finance detection
    legal_email = ProcessedEmail(
        metadata=create_test_email(
            body="We hereby agree to the binding contract terms and legal obligations."
        ),
        priority=PriorityScore(
            score=75,
            priority_level=PriorityLevel.HIGH,
            factors={},
            confidence=0.9
        )
    )
    is_critical = LegalFinanceDetector().check_legal_finance_content_urgent(legal_email)
    
    verifier.test(
        "Legal content detection",
        is_critical,
        "Legal keywords in urgent email should be flagged"
    )
    
    # ============================================================
    # SECTION 6: Metrics Tracking
    # ============================================================
    print("\n📊 SECTION 6: Metrics Tracking")
    print("-" * 70)
    
    # Test approval tracking
    try:
        metrics_tracker.log_approval_decision(
            draft_id="test_draft_1",
            email_id="test_email_1",
            subject="Test Subject",
            recipient="test@example.com",
            accepted=True,
            edited=False
        )
        verifier.test("Approval tracking", True)
    except Exception as e:
        verifier.test("Approval tracking", False, str(e))
    
    # Test VIP miss tracking
    try:
        metrics_tracker.log_vip_miss(
            email_id="test_vip_1",
            vip_email="ceo@company.com",
            subject="Important Meeting",
            actual_priority="medium",
            expected_priority="high",
            reason="Urgency keywords missed"
        )
        verifier.test("VIP miss tracking", True)
    except Exception as e:
        verifier.test("VIP miss tracking", False, str(e))
    
    # Test hallucination tracking
    try:
        metrics_tracker.log_hallucination(
            email_id="test_email_2",
            draft_id="test_draft_2",
            hallucination_type="fact",
            description="Invented meeting time",
            severity="medium"
        )
        verifier.test("Hallucination tracking", True)
    except Exception as e:
        verifier.test("Hallucination tracking", False, str(e))
    
    # Test risk detection tracking
    try:
        metrics_tracker.log_risk_detection(
            email_id="test_email_3",
            risk_type="pii",
            severity="high",
            blocked=True,
            false_positive=False
        )
        verifier.test("Risk detection tracking", True)
    except Exception as e:
        verifier.test("Risk detection tracking", False, str(e))
    
    # Test metrics report generation
    try:
        report = metrics_tracker.generate_comprehensive_report(days=30)
        verifier.test(
            "Metrics report generation",
            all(key in report for key in ['approval_metrics', 'vip_miss_metrics', 
                                         'hallucination_metrics', 'risk_detection_metrics']),
            "All metrics sections present"
        )
    except Exception as e:
        verifier.test("Metrics report generation", False, str(e))
    
    # ============================================================
    # SECTION 7: Evidence & Traceability
    # ============================================================
    print("\n🔍 SECTION 7: Evidence & Traceability")
    print("-" * 70)
    
    # Check priority score includes evidence
    verifier.test(
        "Priority score includes evidence",
        len(priority.evidence) > 0,
        f"{len(priority.evidence)} evidence items"
    )
    
    verifier.test(
        "Priority score includes reasoning",
        bool(priority.reasoning),
        priority.reasoning[:50]
    )
    
    verifier.test(
        "Priority score includes confidence",
        0.0 <= priority.confidence <= 1.0,
        f"Confidence: {priority.confidence}"
    )
    
    # Check classification includes notes
    verifier.test(
        "Classification includes notes",
        bool(classification.notes),
        classification.notes[:50]
    )
    
    # ============================================================
    # SECTION 8: Edge Cases
    # ============================================================
    print("\n⚠️ SECTION 8: Edge Cases")
    print("-" * 70)
    
    # Test conflict resolution (multiple emails from same sender)
    conflict_resolver = ConflictResolver()
    email1 = ProcessedEmail(
        metadata=create_test_email(sender="same@sender.com")
    )
    email1.metadata.date = datetime.now() - timedelta(hours=2)
    
    email2 = ProcessedEmail(
        metadata=create_test_email(sender="same@sender.com")
    )
    email2.metadata.date = datetime.now()
    
    conflicts = conflict_resolver.check_multiple_from_same_sender([email1, email2])
    verifier.test(
        "Conflict detection (same sender)",
        "same@sender.com" in conflicts,
        f"Found {len(conflicts)} conflicts"
    )
    
    active = conflict_resolver.resolve_conflicts(conflicts)
    verifier.test(
        "Conflict resolution (latest email)",
        len(active) == 1 and active[0].metadata.message_id == email2.metadata.message_id,
        "Should keep only the latest email"
    )
    
    # Test DND mode
    dnd_handler = DNDHandler()
    has_alert, reason = dnd_handler.check_tool_alert(can_send=False)
    verifier.test(
        "DND mode / Tool alert",
        has_alert,
        reason
    )
    
    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    verifier.print_summary()
    
    # Return exit code
    return 0 if verifier.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
