"""
S3: Priority Scoring Engine
Calculates priority score based on multiple factors
"""
import logging
from datetime import datetime, timedelta
from config import Config
from models import (
    PriorityScore, PriorityLevel, EmailMetadata,
    ClassificationResult, IntentDetection
)

logger = logging.getLogger(__name__)


class PriorityScorer:
    """Calculates email priority scores"""
    
    def __init__(self):
        self.threshold = Config.PRIORITY_THRESHOLD
    
    def calculate_score(self,
                       metadata: EmailMetadata,
                       classification: ClassificationResult,
                       intent: IntentDetection) -> PriorityScore:
        """
        S3: Priority Scoring Engine
        
        Calculates composite priority score (0-100) based on:
        - Sender importance (VIP, team, etc.)
        - Urgency keywords
        - Deadline proximity
        - Question/action required
        - Email age
        - Hidden urgency detection (PRD requirement)
        """
        logger.debug(f"Calculating priority for: {metadata.subject}")
        
        factors = {}
        score = 0
        evidence = []
        
        # Factor 1: Sender importance (0-40 points)
        sender_score = self._score_sender(classification)
        factors['sender_importance'] = sender_score
        score += sender_score
        if sender_score > 20:
            evidence.append(f"Sender: {classification.sender_type.value}")
        
        # Factor 2: Urgency keywords (0-20 points)
        urgency_score = self._score_urgency(intent)
        factors['urgency_keywords'] = urgency_score
        score += urgency_score
        if intent.urgency_keywords:
            evidence.append(f"Urgent keywords: {', '.join(intent.urgency_keywords[:3])}")
        
        # Factor 3: Action required (0-15 points)
        action_score = self._score_action(intent)
        factors['action_required'] = action_score
        score += action_score
        if intent.action_required:
            evidence.append("Action required")
        
        # Factor 4: Email age (0-10 points)
        age_score = self._score_age(metadata.date)
        factors['email_age'] = age_score
        score += age_score
        
        # Factor 5: Thread context (0-10 points)
        thread_score = self._score_thread(metadata)
        factors['thread_context'] = thread_score
        score += thread_score
        
        # Factor 6: Special categories (0-5 points bonus)
        category_score = self._score_category(intent)
        factors['special_category'] = category_score
        score += category_score
        
        # Factor 7: Hidden urgency detection (PRD requirement)
        hidden_urgency, hidden_evidence = self._detect_hidden_urgency(metadata, intent)
        if hidden_urgency:
            factors['hidden_urgency'] = 15
            score += 15
            evidence.extend(hidden_evidence)
        
        # Ensure score is within 0-100
        score = max(0, min(100, int(score)))
        
        # Determine priority level
        priority_level = self._determine_level(score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(score, factors, priority_level, hidden_urgency)
        
        # Calculate confidence
        confidence = self._calculate_confidence(factors, intent)
        
        result = PriorityScore(
            score=score,
            priority_level=priority_level,
            factors=factors,
            reasoning=reasoning,
            confidence=confidence,
            evidence=evidence,
            hidden_urgency=hidden_urgency
        )
        
        logger.info(f"Priority score: {score}/100 ({priority_level.value}) - Hidden urgency: {hidden_urgency}")
        return result
    
    def _score_sender(self, classification: ClassificationResult) -> int:
        """Score based on sender importance (0-40)"""
        if classification.is_vip:
            return 40
        
        sender_scores = {
            'vip': 40,
            'team': 30,
            'customer': 25,
            'vendor': 15,
            'unknown': 5,
            'spam': 0
        }
        
        return sender_scores.get(classification.sender_type.value, 5)
    
    def _score_urgency(self, intent: IntentDetection) -> int:
        """Score based on urgency keywords (0-20)"""
        urgency_count = len(intent.urgency_keywords)
        
        if urgency_count == 0:
            return 0
        elif urgency_count == 1:
            return 10
        elif urgency_count == 2:
            return 15
        else:
            return 20
    
    def _score_action(self, intent: IntentDetection) -> int:
        """Score based on action required (0-15)"""
        score = 0
        
        if intent.action_required:
            score += 10
        
        if intent.question_detected:
            score += 5
        
        return min(score, 15)
    
    def _score_age(self, email_date: datetime) -> int:
        """Score based on email age (0-10) - newer = higher"""
        now = datetime.now(email_date.tzinfo) if email_date.tzinfo else datetime.now()
        age = now - email_date
        
        # Less than 1 hour = 10 points
        if age < timedelta(hours=1):
            return 10
        # Less than 4 hours = 8 points
        elif age < timedelta(hours=4):
            return 8
        # Less than 24 hours = 5 points
        elif age < timedelta(days=1):
            return 5
        # Less than 3 days = 2 points
        elif age < timedelta(days=3):
            return 2
        # Older = 0 points
        else:
            return 0
    
    def _score_thread(self, metadata: EmailMetadata) -> int:
        """Score based on thread context (0-10)"""
        score = 0
        
        # If it's a reply (has Re: in subject)
        if metadata.subject.lower().startswith('re:'):
            score += 5
        
        # If user is in To: (not just CC)
        # This would require knowing user's email - simplified here
        if metadata.recipients:
            score += 3
        
        # Has attachments
        if metadata.has_attachments:
            score += 2
        
        return min(score, 10)
    
    def _score_category(self, intent: IntentDetection) -> int:
        """Score based on special categories (0-5 bonus)"""
        score = 0
        
        # Legal or finance = high priority bonus
        if 'legal' in intent.intents:
            score += 5
        elif 'finance' in intent.intents:
            score += 5
        # Complaint = medium priority bonus
        elif 'complaint' in intent.intents:
            score += 3
        
        return min(score, 5)
    
    def _determine_level(self, score: int) -> PriorityLevel:
        """
        S4: High Priority? Decision
        
        Determines priority level based on score
        """
        if score >= self.threshold:
            return PriorityLevel.HIGH
        elif score >= 50:
            return PriorityLevel.MEDIUM
        elif score >= 30:
            return PriorityLevel.LOW
        else:
            return PriorityLevel.NOT_REQUIRED
    
    def _generate_reasoning(self, score: int, factors: dict,
                           level: PriorityLevel, hidden_urgency: bool = False) -> str:
        """Generate human-readable reasoning for priority score"""
        reasons = []
        
        # Hidden urgency flag
        if hidden_urgency:
            reasons.append("⚠️ HIDDEN URGENCY DETECTED")
        
        # Sort factors by score
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        
        # Add top contributors
        for factor_name, factor_score in sorted_factors:
            if factor_score > 0:
                reason = self._factor_to_reason(factor_name, factor_score)
                if reason:
                    reasons.append(reason)
        
        reasoning = f"Priority: {level.value.upper()} ({score}/100)"
        if reasons:
            reasoning += " - " + ", ".join(reasons[:4])  # Top 4 reasons
        
        return reasoning
    
    def _detect_hidden_urgency(self, metadata: EmailMetadata, 
                               intent: IntentDetection) -> tuple[bool, list]:
        """
        Detect hidden urgency: polite emails with urgent deadlines (PRD requirement)
        Returns: (is_hidden_urgency, evidence_list)
        """
        evidence = []
        
        # Check for polite language without obvious urgency keywords
        polite_indicators = ['please', 'kindly', 'would you', 'could you', 
                            'at your convenience', 'when possible']
        deadline_indicators = ['deadline', 'due date', 'by end of', 'before',
                              'tomorrow', 'today', 'asap', 'eod', 'eow']
        
        body_lower = metadata.body_text.lower()
        subject_lower = metadata.subject.lower()
        combined_text = body_lower + " " + subject_lower
        
        # Check for polite language
        is_polite = any(phrase in combined_text for phrase in polite_indicators)
        
        # Check for deadline mentions
        has_deadline = any(word in combined_text for word in deadline_indicators)
        
        # Check for low urgency keywords but deadline present
        has_low_urgency_keywords = len(intent.urgency_keywords) <= 1
        
        # Hidden urgency: polite + deadline + low explicit urgency
        if is_polite and has_deadline and has_low_urgency_keywords:
            evidence.append("Polite tone with deadline detected")
            if 'tomorrow' in combined_text or 'today' in combined_text:
                evidence.append("Immediate deadline: today/tomorrow")
            return True, evidence
        
        return False, []
    
    def _calculate_confidence(self, factors: dict, intent: IntentDetection) -> float:
        """Calculate confidence level in priority assessment"""
        confidence = 0.7  # Base confidence
        
        # High confidence if multiple strong signals
        strong_signals = sum(1 for score in factors.values() if score >= 10)
        if strong_signals >= 3:
            confidence = 0.95
        elif strong_signals >= 2:
            confidence = 0.85
        elif strong_signals >= 1:
            confidence = 0.75
        
        # Lower confidence if intent is unclear
        if intent.confidence < 0.5:
            confidence *= 0.9
        
        return min(1.0, confidence)
    
    def _factor_to_reason(self, factor_name: str, score: int) -> str:
        """Convert factor name and score to readable reason"""
        reason_map = {
            'sender_importance': f"Important sender (+{score})",
            'urgency_keywords': f"Urgent keywords (+{score})",
            'action_required': f"Action needed (+{score})",
            'email_age': f"Recent email (+{score})",
            'thread_context': f"Active thread (+{score})",
            'special_category': f"Special category (+{score})",
            'hidden_urgency': f"Hidden urgency (+{score})"
        }
        
        return reason_map.get(factor_name, "")
