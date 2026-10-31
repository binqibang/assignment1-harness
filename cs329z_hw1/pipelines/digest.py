from cs329z_hw1.pipelines.priority import format_email
from cs329z_hw1.pipelines.prompts import DIGEST_PROMPT
from cs329z_hw1.types import Email, LMCallable


def generate_threads(emails: list[Email], email_priority: dict[str, str]) -> tuple[str]:
    urgent_threads = []
    normal_threads = []

    for email in emails:
        priority = email_priority[email['id']] 
        if priority == 'urgent':
            _, lines = format_email(email)
            lines.append('---')
            urgent_threads.append('\n'.join(lines))
        elif priority == 'normal' or priority == 'unknown':
            _, lines = format_email(email)
            lines.append('---')
            normal_threads.append('\n'.join(lines))
        else:
            continue

    return ('\n'.join(urgent_threads), '\n'.join(normal_threads))


def build_messages(emails: list[Email], email_priority: dict[str, str]) -> list[dict]:
    urgent, normal = generate_threads(emails, email_priority)
    messages = [
        {'role': 'system', 'content': DIGEST_PROMPT},
        {
            'role': 'user', 
            'content': f'Urgent Threads:\n{urgent}\nNormal Threads:\n{normal}'
        }
    ]
    return messages
    

def run(emails: list[Email], email_priority: dict[str, str], lm: LMCallable) -> str:
    messages = build_messages(emails, email_priority)
    reply = lm(messages)
    return reply