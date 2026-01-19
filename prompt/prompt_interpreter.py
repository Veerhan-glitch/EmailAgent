"""
S0: Prompt Interpretation
Converts user natural language command into structured agent instructions
"""

import logging
import json
from typing import Dict, Any
from LLM.llm_adapter import LLMAdapter
import re
import json
from config import Config
import re
from typing import List, Dict, Any
# Gemini SDK (optional)
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)
def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class PromptInterpreter:
    """Interprets user prompt into scope + actions"""
    _NUM_WORDS = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10
    }

    _email_regex = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
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

    def interpret(self, user_prompt: str) -> Dict[str, Any]:
        """
        Interpret user command into structured plan.
        Always returns a valid plan using:
        Gemini → safe defaults
        """
        logger.info(f"Interpreting user prompt: {user_prompt}")

        plan: Dict[str, Any] = {}

        # 1️⃣ Gemini interpretation (minimal prompt)
        if self.use_gemini:
            context = self._build_context(user_prompt)
            plan = {}

            # 1️⃣ Try Gemini first
            if self.use_gemini:
                try:
                    plan = self._interpret_with_gemini(context)
                except Exception as e:
                    logger.error(f"Gemini failed: {e}")

            # 2️⃣ Ollama fallback ONLY if Gemini failed
            # if not plan:
            #     logger.warning("Falling back to Ollama for prompt interpretation")

            #     ollama_prompt = self._ollama_prompt(user_prompt)
            #     ollama_output = self.ollama.generate_with_ollama(ollama_prompt)

            #     if ollama_output:
            #         try:
            #             raw = self.extract_json(ollama_output)

            #             if not raw:
            #                 logger.error("Ollama returned non-parseable JSON")
            #                 plan = {}
            #             else:
            #                 plan = self._expand_ollama_plan(raw)
            #             plan = self._expand_ollama_plan(raw)
            #         except json.JSONDecodeError:
            #             logger.error("Ollama returned invalid JSON")
            #             plan = {}

        if plan:
            plan = self._repair_plan(plan)

        # 2️⃣ Fallback defaults (ALWAYS)
        if not plan:
            logger.warning("Using fallback interpretation defaults")
            plan = self._default_plan(user_prompt)

        logger.info(f"✓ Interpreted plan: {plan}")

        def _normalize_emails(value):
            if not value:
                return []
            if isinstance(value, list):
                return value
            return [v.strip() for v in value.split(",") if v.strip()]

        compose = plan.get("compose") or {}

        compose["to"] = _normalize_emails(compose.get("to"))
        compose["cc"] = _normalize_emails(compose.get("cc"))
        compose["bcc"] = _normalize_emails(compose.get("bcc"))

        # subject must never be None
        if not compose.get("subject"):
            body_intent = compose.get("body_intent", "Message")
            compose["subject"] = (
                body_intent.capitalize() if body_intent else "Message"
            )

        plan["compose"] = compose

        return plan

    # ------------------------------------------------------------------
    # Gemini interpretation (INTENTIONALLY LOW TOKEN)
    # ------------------------------------------------------------------

    def _interpret_with_gemini(self, context: str) -> Dict[str, Any]:
        if not self.gemini_client:
            return {}

        response = self.gemini_client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=context
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
            return {}

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            logger.error("Gemini returned invalid JSON")
            return {}

    # ------------------------------------------------------------------
    # Prompt builder (STRICT JSON)
    # ------------------------------------------------------------------

    def _build_context(self, user_prompt: str) -> str:
        """
        Very strict JSON-only prompt.
        """
        return (
            "You are an advanced email AI assistant.\n"
            "Convert the user's natural language request into STRICT JSON only.\n\n"

            "UNDERSTAND these user intents:\n"
            "1. SEARCH/FILTER: 'show', 'find', 'get', 'check', 'list', 'what emails'\n"
            "2. COMPOSE NEW: 'write to', 'send email to', 'compose', 'create email', 'email X about'\n"
            "3. REPLY: 'reply to', 'respond to', 'answer'\n"
            "4. SUMMARIZE: 'summarize', 'give me summary', 'what's the gist', 'tldr', 'brief'\n"
            "5. ORGANIZE: 'archive', 'delete', 'label', 'mark as read'\n"
            "6. ANALYTICS: 'how many', 'who sent most', 'count', 'statistics'\n\n"

            "JSON schema (output ONLY valid JSON, no markdown, no explanation):\n"
            "{\n"
            '  "intent": "search" | "compose" | "reply" | "summarize" | "organize" | "analytics",\n'
            '  "scope": {\n'
            '    "time_range_days": number,\n'
            '    "max_results": number,\n'
            '    "query": string,\n'
            '    "sender": string,\n'
            '    "subject_contains": string,\n'
            '    "has_attachment": boolean\n'
            "  },\n"
            '  "actions": {\n'
            '    "draft_replies": boolean,\n'
            '    "compose_new": boolean,\n'
            '    "require_approval": boolean,\n'
            '    "only_urgent": boolean,\n'
            '    "include_followups": boolean,\n'
            '    "summarize": boolean,\n'
            '    "mark_as_read": boolean\n'
            "  },\n"
            '  "compose": {\n'
            '    "to": string,\n'
            '    "subject": string,\n'
            '    "body_intent": string,\n'
            '    "cc": string\n'
            '    "bcc": string\n'
            "  },\n"
            '  "target": {\n'
            '    "sender_email": string,\n'
            '    "latest_only": boolean\n'
            "  }\n"
            "}\n\n"

            "INTERPRETATION RULES:\n"
            "- Output valid JSON only (no markdown, no prose)\n"
            "- Make reasonable defaults if unclear\n"
            "- Replies and composed emails ALWAYS require approval\n\n"

            "- Time mapping:\n"
            "  'today'=1, 'yesterday'=2, 'week'=7, 'month'=30, 'year'=365\n\n"

            "- Urgency rules:\n"
            "  'urgent', 'important', 'critical', 'asap' → only_urgent = true\n\n"

            "- Compose rules:\n"
            "  'write to X', 'send to X', 'email X about Y' → intent=compose, compose_new=true\n"
            "  Extract recipient email, subject, and body intent\n\n"

            "- Reply rules:\n"
            "  'reply to X', 'respond to X' → intent=reply, draft_replies=true\n"
            "  'create drafts', 'generate drafts', 'draft replies' → draft_replies=true\n"
            "  If replying, extract sender_email when possible\n\n"

            "- Search/filter rules:\n"
            "  'from X', 'by X', 'sent by X' → sender or sender_email\n"
            "  'about X', 'regarding X', 'subject contains X' → subject_contains\n"
            "  'with attachment', 'has files' → has_attachment=true\n\n"

            "- Summarize rules:\n"
            "  'summarize', 'summary', 'tldr', 'brief' → summarize=true\n"
            "  If summarizing, do NOT draft replies\n"
            "  'summarize 1 email' → max_results=1\n\n"

            "- Latest rules:\n"
            "  'latest', 'most recent', 'newest' → latest_only=true\n\n"

            "- Analytics rules:\n"
            "  'how many', 'who sent most', 'count', 'statistics' → intent=analytics\n\n"

            f"USER REQUEST:\n\"{user_prompt}\"\n\n"
            "Output ONLY the JSON:"
        )



    def _repair_plan(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        scope = raw.get("scope", {}) or {}
        actions = raw.get("actions", {}) or {}
        target = raw.get("target", {}) or {}

        intent = raw.get("intent")
        compose = raw.get("compose")

        return {
            "intent": intent,
            "scope": {
                "time_range_days": _safe_int(scope.get("time_range_days"), 3),
                "max_results": _safe_int(scope.get("max_results"), 5),
                "query": scope.get("query") or "",
            },
            "actions": {
                "draft_replies": bool(actions.get("draft_replies", False)),
                "compose_new": bool(actions.get("compose_new", intent == "compose")),
                "require_approval": True,
                "only_urgent": bool(actions.get("only_urgent", False)),
                "include_followups": bool(actions.get("include_followups", False)),
            },
            "compose": compose,
            "target": {
                "sender_email": target.get("sender_email"),
                "latest_only": bool(target.get("latest_only", True))
            }
        }
    
    def _expand_ollama_plan(self, data: dict) -> dict:
        return {
            "intent": data.get("intent", "search"),
            "scope": {
                "time_range_days": data.get("time_range_days", 7),
                "max_results": data.get("max_results", 10),
                "query": "",
                "sender": "",
                "subject_contains": "",
                "has_attachment": False
            },
            "actions": {
                "draft_replies": data.get("draft_replies", False),
                "compose_new": data.get("compose_new", False),
                "require_approval": True,
                "only_urgent": data.get("only_urgent", False),
                "include_followups": False,
                "summarize": False,
                "mark_as_read": False
            },
            "compose": {
                "to": "",
                "subject": "",
                "body_intent": "",
                "cc": ""
            },
            "target": {
                "sender_email": data.get("sender_email"),
                "latest_only": data.get("latest_only", False)
            }
        }
    
    @staticmethod
    def extract_json(text: str) -> dict | None:
        """
        Extract the first valid JSON object from LLM output.
        Works even if model adds text before/after JSON.
        """
        if not text:
            return None

        # Find the first {...} block
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None

        json_str = match.group(0)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    def _ollama_prompt(self, user_prompt: str) -> str:
        return f"""
    You are a command classifier.

    Return ONLY a JSON object.
    NO explanations.
    NO markdown.
    NO text outside JSON.

    JSON schema:
    {{
    "intent": "search" | "compose" | "reply" | "summarize" | "organize" | "analytics",
    "draft_replies": boolean,
    "compose_new": boolean,
    "only_urgent": boolean,
    "latest_only": boolean,
    "max_results": number,
    "sender_email": string
    }}

    User request:
    "{user_prompt}"
    """




    # small number words map
    def _filter_valid_emails(self, items):
        if not items:
            return []
        return [x for x in items if self._email_regex.fullmatch(x)]

    
    @staticmethod
    def _word_to_num(token: str) -> int | None:
        token = token.lower().strip()
        if token.isdigit():
            return int(token)
        return self._NUM_WORDS.get(token)

    def _find_number_after_keyword(self, text: str, keyword: str) -> int | None:
        # looks for "keyword N" or "keyword N mails" or "keyword N mail(s)"
        pattern = rf"{keyword}\s+(?:(\d+)|({'|'.join(self._NUM_WORDS.keys())}))"
        m = re.search(pattern, text, flags=re.I)
        if not m:
            return None
        if m.group(1):
            return int(m.group(1))
        if m.group(2):
            return self._NUM_WORDS.get(m.group(2).lower())
        return None

    def _extract_emails(self, text: str) -> List[str]:
        return self._email_regex.findall(text)

    @staticmethod
    def _split_recipients_fragment(fragment: str) -> List[str]:
        # Accept comma, and, &, ; separators — return stripped tokens
        parts = re.split(r",|\band\b|&|;|\bplus\b", fragment, flags=re.I)
        return [p.strip() for p in parts if p.strip()]

    def _extract_recipients_from_phrase(self, text: str) -> Dict[str, List[str]]:
        """
        Extract to/cc/bcc lists. Strategy:
        - First collect all explicit emails.
        - Then, parse natural phrases:
        'to X and Y', 'put X in cc', 'with X in bcc', 'cc: ...', 'bcc: ...'
        - Prefer emails; for name-like tokens (no @) keep them as strings (caller can map them later).
        """
        out = {"to": [], "cc": [], "bcc": []}

        # quick email tokens
        emails = self._extract_emails(text)

        # capture explicit "to ...", "cc ...", "bcc ..." or "put ... in cc"
        # patterns intentionally liberal
        # to:
        to_phrases = re.findall(r"(?:to|send(?: an email)? to|email(?: to)?)\s+([^\n,;]+?)(?=(?:\s+put|\s+with|\s+cc|\s+bcc|\s+asking|\s+saying|\s+about|$))", text, flags=re.I)
        for frag in to_phrases:
            tokens = self._split_recipients_fragment(frag)
            for t in tokens:
                if self._email_regex.search(t):
                    out["to"].extend(self._email_regex.findall(t))
                else:
                    out["to"].append(t)

        # cc:
        cc_phrases = re.findall(r"(?:cc[:\s]|put\s+(.+?)\s+in\s+cc|cc\s+to\s+)([^\n,;]+?)?(?=(?:\s+with|\s+bcc|\s+asking|\s+saying|\s+about|$))", text, flags=re.I)
        # cc_phrases can be mixed due to groups; flatten
        for elem in cc_phrases:
            # elem might be tuple from groups; pick non-empty
            frag = elem if isinstance(elem, str) else next((e for e in elem if e and e.strip()), "")
            if not frag:
                continue
            for t in self._split_recipients_fragment(frag):
                if self._email_regex.search(t):
                    out["cc"].extend(self._email_regex.findall(t))
                else:
                    out["cc"].append(t)

        # bcc:
        bcc_phrases = re.findall(r"(?:bcc[:\s]|put\s+(.+?)\s+in\s+bcc|bcc\s+to\s+)([^\n,;]+?)?(?=(?:\s+asking|\s+saying|\s+about|$))", text, flags=re.I)
        for elem in bcc_phrases:
            frag = elem if isinstance(elem, str) else next((e for e in elem if e and e.strip()), "")
            if not frag:
                continue
            for t in self._split_recipients_fragment(frag):
                if self._email_regex.search(t):
                    out["bcc"].extend(self._email_regex.findall(t))
                else:
                    out["bcc"].append(t)

        # If no explicit "to" phrases but emails exist, assume emails are 'to'
        if not out["to"] and emails:
            # prefer all emails not already in cc/bcc
            out["to"] = [e for e in emails if e not in out["cc"] + out["bcc"]]

        # deduplicate while preserving order
        for k in ["to", "cc", "bcc"]:
            seen = set()
            cleaned = []
            for v in out[k]:
                if v in seen:
                    continue
                seen.add(v)
                cleaned.append(v)
            out[k] = cleaned

        return out

    @staticmethod
    def _extract_subject(text: str) -> str | None:
        # look for explicit subject patterns
        m = re.search(r"subject[:\s-]+\"?([^\"\n]+)\"?", text, flags=re.I)
        if m:
            return m.group(1).strip()
        m = re.search(r"subject\s+is\s+([^\n,]+)", text, flags=re.I)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _extract_body_intent(text: str) -> str:
        # after markers such as 'asking', 'saying', 'telling', 'about', 'that', 'asking if'
        m = re.search(r"(?:asking|asking\s+if|asking\s+about|saying|telling|about|regarding|asking\:)\s+(.*)", text, flags=re.I)
        if m:
            # trim trailing connectors
            body = m.group(1).strip()
            # cut off trailing "to <someone>" phrases that might have been captured
            body = re.split(r"\s+to\s+[^\s,]+", body, maxsplit=1)[0].strip()
            # remove any trailing 'with cc' or 'with bcc' etc
            body = re.split(r"(?:\s+with\s+cc|\s+with\s+bcc|\s+put\s+.*\s+in\s+cc|\s+put\s+.*\s+in\s+bcc)", body, flags=re.I)[0].strip()
            return body
        return ""

    @staticmethod
    def _time_range_days_from_text(text: str) -> int:
        text = text.lower()
        if "today" in text:
            return 1
        if "yesterday" in text:
            return 2
        if "week" in text:
            return 7
        if "month" in text:
            return 30
        if "year" in text:
            return 365
        return 3  # default

    @staticmethod
    def _detect_flags(text: str) -> Dict[str, bool]:
        flags = {
            "only_urgent": any(k in text for k in ["urgent", "asap", "important", "immediately", "critical"]),
            "include_followups": bool(re.search(r"follow[- ]?up|follow up|followup", text, flags=re.I)),
            "require_approval": True  # keep approval True by default for safety
        }
        return flags

    # ---- main smart fallback plan ----
    def _default_plan(self, user_prompt: str) -> Dict[str, Any]:
        """
        Smart NLP fallback when LLMs fail.
        Returns structured plan dict compatible with the rest of the pipeline.
        """
        text = user_prompt.strip()
        text_l = text.lower()

        # Intent detection (rule-based)
        if any(k in text_l for k in ["send ", "send a mail", "email ", "write to", "compose", "send to", "mail to", "send an email"]):
            intent = "compose"
        elif any(k in text_l for k in ["reply", "respond", "answer"]):
            intent = "reply"
        elif any(k in text_l for k in ["show", "list", "get", "find", "search"]):
            intent = "search"
        elif any(k in text_l for k in ["summarize", "summary", "tldr"]):
            intent = "summarize"
        else:
            # conservative default: search
            intent = "search"

        # scope: time range and max results
        time_range_days = self._time_range_days_from_text(text_l)
        max_results = 5
        latest_only = False

        # look for explicit "last X" patterns (digits or words)
        num = self._find_number_after_keyword(text_l, r"last")
        if num:
            max_results = num
            latest_only = True
        else:
            # also look for "last N mails" variant
            m = re.search(r"last\s+(\d+)\s+(?:mails|emails|threads)", text_l)
            if m:
                max_results = int(m.group(1))
                latest_only = True
            elif "latest" in text_l or "most recent" in text_l:
                max_results = 1
                latest_only = True

        # recipients extraction
        recs = self._extract_recipients_from_phrase(text)

        # subject and body intent
        subject = self._extract_subject(text) or ""
        body_intent = self._extract_body_intent(text)

        # if subject empty, derive from body_intent
        if not subject and body_intent:
            # make a short subject (first 6-8 words)
            subject = " ".join(body_intent.split()[:8]).strip().capitalize()
            if len(subject) == 0:
                subject = "Message"

        if not subject:
            # final fallback
            subject = "Message"

        # detect other flags
        flags = self._detect_flags(text_l)

        # assemble plan
        plan = {
            "intent": intent,
            "scope": {
                "time_range_days": time_range_days,
                "max_results": max_results,
                "query": ""
            },
            "actions": {
                "draft_replies": intent == "reply",
                "compose_new": intent == "compose",
                "require_approval": flags["require_approval"],
                "only_urgent": flags["only_urgent"],
                "include_followups": flags["include_followups"]
            },
            "compose": {
                "to": recs["to"],
                "cc": recs["cc"],
                "bcc": recs["bcc"],
                "subject": subject,
                "body_intent": body_intent
            },
            "target": {
                "sender_email": None,
                "latest_only": latest_only
            }
        }

        # debug-friendly single-line log (caller can log plan)
        compose = plan.get("compose", {})

        compose["to"] = self._filter_valid_emails(compose.get("to"))
        compose["cc"] = self._filter_valid_emails(compose.get("cc"))
        compose["bcc"] = self._filter_valid_emails(compose.get("bcc"))

        plan["compose"] = compose
        return plan
