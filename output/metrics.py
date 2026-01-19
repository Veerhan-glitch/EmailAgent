"""
F2: Metrics Panel Generator
"""
import logging
from typing import Dict, Any
from collections import Counter
from models import ProcessingBatch, ProcessedEmail, MetricsReport

logger = logging.getLogger(__name__)


class MetricsGenerator:
    """Generates metrics and statistics"""
    
    def generate_metrics(self, batch: ProcessingBatch) -> MetricsReport:
        """
        F2: Metrics Panel
        
        Calculates and formats metrics for display (PRD enhanced)
        """
        logger.info("Generating metrics...")
        
        # Count by priority
        high_priority = sum(1 for e in batch.emails 
                          if e.priority and e.priority.priority_level.value == 'high')
        medium_priority = sum(1 for e in batch.emails 
                             if e.priority and e.priority.priority_level.value == 'medium')
        low_priority = sum(1 for e in batch.emails 
                          if e.priority and e.priority.priority_level.value == 'low')
        
        # Count drafts and follow-ups
        drafts_created = sum(1 for e in batch.emails if e.draft_reply)
        follow_ups_scheduled = sum(len(e.follow_ups) for e in batch.emails)
        
        # Count blocked
        blocked_items = sum(1 for e in batch.emails if e.is_blocked)
        
        # Count by category
        categories = Counter(e.category.value for e in batch.emails)
        
        # Count VIP emails
        vip_emails = sum(1 for e in batch.emails 
                        if e.classification and e.classification.is_vip)
        
        # Count approval required
        approval_required = sum(1 for e in batch.emails 
                               if e.draft_reply and e.draft_reply.requires_approval)
        
        # PRD metrics
        missed_vip = 0  # Would need tracking system
        risk_detection_count = sum(len(e.security_flags) for e in batch.emails)
        hidden_urgency_count = sum(1 for e in batch.emails 
                                  if e.priority and e.priority.hidden_urgency)
        reply_all_risks = sum(1 for e in batch.emails 
                             if e.draft_reply and e.draft_reply.reply_all_risk)
        hallucination_flags = 0  # Would need validation system
        
        # Calculate time saved (estimate)
        time_saved = self._estimate_time_saved(batch.emails)
        
        metrics = MetricsReport(
            total_emails=len(batch.emails),
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
            drafts_created=drafts_created,
            follow_ups_scheduled=follow_ups_scheduled,
            blocked_items=blocked_items,
            categories=dict(categories),
            time_saved_minutes=time_saved,
            vip_emails=vip_emails,
            approval_required_count=approval_required,
            missed_vip_emails=missed_vip,
            risk_detection_count=risk_detection_count,
            hidden_urgency_count=hidden_urgency_count,
            reply_all_risks=reply_all_risks,
            hallucination_flags=hallucination_flags
        )
        
        logger.info(f"✓ Metrics generated: {metrics.total_emails} emails processed")
        return metrics
    
    def _estimate_time_saved(self, emails) -> int:
        """Estimate time saved in minutes"""
        # Rough estimates:
        # - Reading/triaging 1 email: 2 min
        # - Drafting reply: 5 min
        # - Categorizing: 1 min
        
        time_saved = 0
        
        for email in emails:
            # Time saved on triage
            time_saved += 2
            
            # Time saved on categorization
            time_saved += 1
            
            # Time saved on drafting
            if email.draft_reply:
                time_saved += 5
            
            # Time saved on follow-up planning
            if email.follow_ups:
                time_saved += 2
        
        return time_saved
    
    def format_metrics_display(self, metrics: MetricsReport) -> str:
        """Format metrics for console display"""
        display = f"""
╔═══════════════════════════════════════════════════════╗
║              EMAIL AGENT METRICS PANEL                  ║
╠═══════════════════════════════════════════════════════╣
║                                                         ║
║  📧 Total Emails Processed:  {metrics.total_emails:>3}                    ║
║                                                         ║
║  🔴 High Priority:            {metrics.high_priority:>3}                    ║
║  🟡 Medium Priority:          {metrics.medium_priority:>3}                    ║
║  🟢 Low Priority:             {metrics.low_priority:>3}                    ║
║                                                         ║
║  ✍️  Drafts Created:          {metrics.drafts_created:>3}                    ║
║  ⏰ Follow-ups Scheduled:     {metrics.follow_ups_scheduled:>3}                    ║
║  🚫 Blocked Items:            {metrics.blocked_items:>3}                    ║
║                                                         ║
║  ⭐ VIP Emails:               {metrics.vip_emails:>3}                    ║
║  ✅ Require Approval:         {metrics.approval_required_count:>3}                    ║
║                                                         ║
║  ⏱️  Estimated Time Saved:    {metrics.time_saved_minutes:>3} minutes            ║
║                                                         ║
╠═══════════════════════════════════════════════════════╣
║  CATEGORIES:                                            ║
"""
        
        for category, count in metrics.categories.items():
            display += f"║    {category.upper():>12}:  {count:>3}                            ║\n"
        
        display += "╚═══════════════════════════════════════════════════════╝"
        
        return display
