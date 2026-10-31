import json

from cs329z_hw1.types import Email, LMCallable
from .prompts import PRIORITY_PROMPT


def format_email(email: Email) -> tuple[str, list[str]]:
    """Converts an Email TypedDict into a human-readable string."""

    # Safely get the 'from' field since it's a reserved keyword 
    # and can't be declared in the TypedDict class body.
    sender = email.get("from", "Unknown")

    # Join the list of recipients into a comma-separated string
    recipients = ", ".join(email.get("to", []))

    # Format the output
    lines = [
        f"From: {sender}",
        f"To: {recipients}",
        f"Date: {email.get('date', '')}",
        f"Subject: {email.get('subject', '')}",
    ]
    if email.get("reply_to"):
        lines.insert(1, f"In-Reply-To: {email['reply_to']}")
        
    lines.append("")  # Blank line before body
    lines.append(email.get("body", ""))

    return "\n".join(lines), lines


def build_messages(email: Email) -> list[dict]:
    formatted_email, _ = format_email(email)
    return [
        {'role': 'system', 'content': PRIORITY_PROMPT},
        {'role': 'user', 'content': f'Please classify this email:\n<email>\n{formatted_email}\n</email>'}
    ]


def run(email: Email, lm: LMCallable) -> dict:
    messages = build_messages(email)
    reply = lm(messages)
    try:
        res = json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        import re
        match = re.search(r'\{.*\}', reply, re.DOTALL) if isinstance(reply, str) else None
        if match:
            try:
                res = json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"category": "unknown", "reason": "Failed to parse JSON from LLM reply."}
        else:
            return {"category": "unknown", "reason": "Invalid JSON response from LLM."}

    if not isinstance(res, dict):
        return {"category": "unknown", "reason": "Parsed JSON is not an object."}

    category = str(res.get("category", "")).strip().lower()
    reason = str(res.get("reason", "")).strip()

    valid_labels = {"urgent", "normal", "ignore"}
    if category not in valid_labels:
        category = "unknown"

    if not reason:
        category = "unknown"
        reason = "No reason provided by the LLM."

    return {"category": category, "reason": reason}