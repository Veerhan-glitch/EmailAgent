"""
S3.5: Thread Summarization Module
Generates short, factual summaries of email threads with decisions and open questions
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import Config
from models import EmailMetadata

# Gemini SDK
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


class ThreadSummarizer:
    """Generates factual summaries of email threads"""
    
    def __init__(self):
        self.use_gemini = Config.GEMINI_ENABLED and bool(Config.GEMINI_API_KEY)
        self.gemini_client = None
        
        if self.use_gemini and genai:
            try:
                self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                logger.info("✓ Thread Summarizer initialized with Gemini AI")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.use_gemini = False
    
    def summarize_thread(self, messages: List[EmailMetadata]) -> Dict[str, Any]:
        """
        S3.5: Thread Summarization
        
        Generates a short, factual summary highlighting:
        - Key discussion points
        - Decisions made
        - Open questions
        - Action items
        
        Args:
            messages: List of EmailMetadata objects in chronological order
        
        Returns:
            Dictionary with summary, decisions, open_questions, and confidence
        """
        if not messages:
            logger.warning("No messages to summarize")
            return self._empty_summary()
        
        logger.info(f"Summarizing thread with {len(messages)} message(s)")
        
        # Sort messages by date
        sorted_messages = sorted(messages, key=lambda m: m.date)
        
        # Try Gemini AI first
        if self.use_gemini and self.gemini_client:
            try:
                summary_result = self._summarize_with_gemini(sorted_messages)
                if summary_result:
                    logger.info("✓ Thread summarized with Gemini AI")
                    return summary_result
            except Exception as e:
                logger.error(f"Gemini summarization failed: {e}")
        
        # Fallback to rule-based summarization
        logger.info("Using rule-based thread summarization")
        return self._summarize_with_rules(sorted_messages)
    
    def _summarize_with_gemini(self, messages: List[EmailMetadata]) -> Optional[Dict[str, Any]]:
        """Use Gemini AI to generate thread summary"""
        if not self.gemini_client:
            return None
        
        # Build context for Gemini
        context = self._build_thread_context(messages)
        
        prompt = f"""Analyze this email thread and provide a structured summary.

{context}

Return a JSON object with EXACTLY this structure (no markdown, no explanation):
{{
  "summary": "2-3 sentence overview of the thread",
  "key_points": ["point 1", "point 2", "point 3"],
  "decisions_made": ["decision 1", "decision 2"],
  "open_questions": ["question 1", "question 2"],
  "action_items": ["action 1", "action 2"],
  "participants": ["name 1", "name 2"],
  "sentiment": "positive" | "neutral" | "negative" | "urgent"
}}

Rules:
- Be factual and concise
- Extract actual decisions (not speculation)
- List only explicit open questions
- Identify clear action items
- Sentiment should reflect overall tone
"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt
            )
            
            raw_text = None
            if hasattr(response, "text") and response.text:
                raw_text = response.text
            else:
                try:
                    raw_text = response.output[0].content[0].text
                except Exception:
                    raw_text = None
            
            if not raw_text:
                return None
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from potential markdown
            json_match = re.search(r'\{[\s\S]*\}', raw_text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                
                # Add metadata
                result['confidence'] = 0.9
                result['method'] = 'gemini_ai'
                result['message_count'] = len(messages)
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini thread summarization error: {e}")
            return None
    
    def _summarize_with_rules(self, messages: List[EmailMetadata]) -> Dict[str, Any]:
        """Rule-based thread summarization fallback"""
        
        # Extract key information
        participants = set()
        all_text = []
        
        for msg in messages:
            participants.add(msg.sender)
            participants.update(msg.recipients)
            all_text.append(msg.subject)
            all_text.append(msg.body_text)
        
        combined_text = " ".join(all_text).lower()
        
        # Detect decisions
        decisions = self._extract_decisions(combined_text)
        
        # Detect open questions
        open_questions = self._extract_questions(messages)
        
        # Detect action items
        action_items = self._extract_action_items(combined_text)
        
        # Generate summary
        latest = messages[-1]
        subject = latest.subject
        
        summary = f"Thread about '{subject}' with {len(messages)} message(s) from {len(participants)} participant(s)."
        
        # Add context
        if decisions:
            summary += f" {len(decisions)} decision(s) made."
        if open_questions:
            summary += f" {len(open_questions)} open question(s)."
        if action_items:
            summary += f" {len(action_items)} action item(s)."
        
        # Detect sentiment
        sentiment = self._detect_sentiment(combined_text)
        
        return {
            'summary': summary,
            'key_points': self._extract_key_points(messages),
            'decisions_made': decisions,
            'open_questions': open_questions,
            'action_items': action_items,
            'participants': list(participants)[:10],  # Limit to 10
            'sentiment': sentiment,
            'confidence': 0.7,
            'method': 'rule_based',
            'message_count': len(messages)
        }
    
    def _build_thread_context(self, messages: List[EmailMetadata]) -> str:
        """Build context string for Gemini"""
        context_parts = []
        
        for i, msg in enumerate(messages, 1):
            context_parts.append(f"Message {i}:")
            context_parts.append(f"From: {msg.sender}")
            context_parts.append(f"Subject: {msg.subject}")
            context_parts.append(f"Date: {msg.date.strftime('%Y-%m-%d %H:%M')}")
            
            # Truncate body for token efficiency
            body = msg.body_text[:500] if msg.body_text else msg.snippet
            context_parts.append(f"Content: {body}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _extract_decisions(self, text: str) -> List[str]:
        """Extract decisions from text"""
        decision_keywords = [
            'decided', 'agreed', 'approved', 'confirmed',
            'will proceed', 'moving forward', 'have chosen',
            'final decision', 'settled on'
        ]
        
        decisions = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in decision_keywords):
                if len(sentence) > 20 and len(sentence) < 200:
                    decisions.append(sentence.capitalize())
                    if len(decisions) >= 5:  # Limit to 5
                        break
        
        return decisions
    
    def _extract_questions(self, messages: List[EmailMetadata]) -> List[str]:
        """Extract open questions from messages"""
        questions = []
        
        for msg in messages:
            text = f"{msg.subject} {msg.body_text}"
            
            # Find sentences with question marks
            sentences = text.split('.')
            for sentence in sentences:
                if '?' in sentence:
                    question = sentence.split('?')[0] + '?'
                    question = question.strip()
                    
                    if len(question) > 10 and len(question) < 200:
                        questions.append(question)
                        if len(questions) >= 5:  # Limit to 5
                            return questions
        
        return questions
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        action_keywords = [
            'please', 'need to', 'should', 'must', 'will',
            'action item', 'todo', 'to do', 'follow up',
            'next step'
        ]
        
        actions = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in action_keywords):
                if len(sentence) > 15 and len(sentence) < 200:
                    actions.append(sentence.capitalize())
                    if len(actions) >= 5:  # Limit to 5
                        break
        
        return actions
    
    def _extract_key_points(self, messages: List[EmailMetadata]) -> List[str]:
        """Extract key discussion points"""
        key_points = []
        
        # Use subject lines as key points
        for msg in messages:
            if msg.subject and msg.subject not in key_points:
                key_points.append(msg.subject)
                if len(key_points) >= 3:
                    break
        
        return key_points
    
    def _detect_sentiment(self, text: str) -> str:
        """Detect overall sentiment of thread"""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
        positive_keywords = ['thanks', 'great', 'excellent', 'perfect', 'appreciate']
        negative_keywords = ['issue', 'problem', 'concern', 'disappointed', 'frustrated']
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'urgent'
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure"""
        return {
            'summary': 'No messages to summarize',
            'key_points': [],
            'decisions_made': [],
            'open_questions': [],
            'action_items': [],
            'participants': [],
            'sentiment': 'neutral',
            'confidence': 0.0,
            'method': 'none',
            'message_count': 0
        }
    
    def summarize_single_email(self, metadata: EmailMetadata) -> Dict[str, Any]:
        """Summarize a single email (convenience method)"""
        return self.summarize_thread([metadata])
