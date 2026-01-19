# Email Agent

AI-powered Email Management System that automates inbox triage, prioritization, drafting, follow-ups, routing and escalation.

## Architecture

This implementation follows a comprehensive processing pipeline with 7 major sections:

1. **Tool Permissions Check** - Validates Gmail API access
2. **Data Ingestion** - Fetches and processes emails
3. **Core Classification Pipeline** - Analyzes and categorizes emails
4. **Edge Case Handling** - Manages conflicts, legal/finance detection, DND mode
5. **Drafting** - Generates reply drafts and follow-ups
6. **Guardrails** - Security checks (PII, domain restrictions, tone enforcement)
7. **Final Output** - Builds response queue and metrics

## Features

### Core Capabilities
- ✅ Sender classification (VIP, team, vendor, customer, spam)
- ✅ Intent detection with keyword extraction
- ✅ Priority scoring (0-100 scale)
- ✅ Email categorization (action, FYI, waiting, spam, legal, finance)
- ✅ Spam filtering
- ✅ AI-powered draft replies
- ✅ Follow-up scheduling
- ✅ Thread mapping

### Security & Guardrails
- 🔒 PII detection
- 🔒 Domain restrictions
- 🔒 Tone enforcement
- 🔒 Approval gates for external emails
- 🔒 Legal/finance escalation

### Edge Case Handling
- ⚠️ Multiple emails from same sender resolution
- ⚠️ Legal/finance content blocking
- ⚠️ DND (Do Not Disturb) mode
- ⚠️ Tool capability alerts

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json` and place in project root

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `GMAIL_CLIENT_ID` - From Google Cloud Console
- `GMAIL_CLIENT_SECRET` - From Google Cloud Console
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - For draft generation

### 4. Run the Agent

```bash
python email_agent.py
```

## Project Structure

```
EmailAgent/
├── config.py                 # Configuration management
├── models.py                 # Data models
├── email_agent.py           # Main orchestrator
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
│
├── tools/                  # External integrations
│   ├── gmail_client.py    # Gmail API wrapper
│   └── permissions.py     # Permission checker
│
├── core/                  # Core processing
│   ├── classifier.py      # Sender classification
│   ├── intent_detector.py # Intent detection
│   ├── priority_scorer.py # Priority scoring
│   ├── categorizer.py     # Email categorization
│   └── spam_filter.py     # Spam detection
│
├── drafting/             # Reply generation
│   ├── reply_drafter.py  # Draft generator
│   ├── tone_preserver.py # Tone checker
│   └── followup_generator.py # Follow-up creation
│
├── edge_cases/          # Edge case handlers
│   ├── conflict_resolver.py # Duplicate resolution
│   ├── legal_detector.py    # Legal/finance detection
│   └── dnd_handler.py       # DND mode handler
│
├── guardrails/         # Security layer
│   ├── pii_detector.py    # PII detection
│   ├── domain_checker.py  # Domain validation
│   └── tone_enforcer.py   # Tone checking
│
└── output/            # Output generation
    ├── queue_builder.py  # Response queue
    └── metrics.py        # Metrics generation
```

## Usage Examples

### Basic Usage

```python
from email_agent import EmailAgent

agent = EmailAgent()

result = agent.run(
    user_command="Handle my inbox from today. Show only urgent items.",
    user_scope={
        'time_range_days': 1,
        'max_results': 50
    }
)
```

### With Custom Filters

```python
result = agent.run(
    user_command="Process unread emails from VIPs",
    user_scope={
        'query': 'is:unread',
        'time_range_days': 7,
        'max_results': 100
    }
)
```

### DND Mode

```python
agent.dnd_handler.set_dnd_mode(True)
agent.dnd_handler.set_auto_responder(True)

result = agent.run(
    user_command="Handle urgent items only",
    user_scope={'time_range_days': 1}
)
```

## Output Format

The agent returns a structured response with:

```json
{
  "queue": {
    "batch_id": "abc123",
    "summary": {
      "total_processed": 42,
      "high_priority": 5,
      "drafts_created": 3,
      "needs_approval": 2,
      "blocked": 1
    },
    "high_priority_emails": [...],
    "draft_replies": [...],
    "follow_ups": [...],
    "blocked_items": [...]
  },
  "metrics": {
    "total_emails": 42,
    "time_saved_minutes": 210,
    "vip_emails": 3,
    "categories": {...}
  }
}
```

## Configuration Options

### Priority Scoring
- `PRIORITY_THRESHOLD`: Score threshold for high priority (default: 70)

### Domains
- `VIP_DOMAINS`: Comma-separated list of VIP domains
- `ALLOWED_DOMAINS`: Domains allowed for external communication
- `BLOCKED_DOMAINS`: Domains to block

### Security
- `REQUIRE_APPROVAL_FOR_EXTERNAL`: Require approval for external emails (default: true)
- `ENABLE_PII_DETECTION`: Enable PII scanning (default: true)
- `ENABLE_DOMAIN_RESTRICTIONS`: Enable domain checking (default: true)
- `ENABLE_TONE_ENFORCEMENT`: Enable tone checking (default: true)

## Success Metrics

The agent tracks:
- ⏱️ Time saved per day
- ✅ % of important emails correctly surfaced
- 📊 Approval rejection rate
- ⭐ Missed VIP items (target: near zero)

## Safety & Compliance

### DO
- ✅ Always show evidence (thread links, message IDs)
- ✅ Default to draft-only for external sending
- ✅ Ask clarifying questions when unclear
- ✅ Batch actions to reduce noise

### DON'T
- ❌ Never send external emails without approval
- ❌ Never hallucinate facts not in context
- ❌ Never guess recipients when ambiguous

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
