"""Onboarding flow for the GitLab Guide chatbot.

Provides the five curated questions presented to first-time users during
the guided onboarding tour.
"""

ONBOARDING_QUESTIONS: list[str] = [
    "What are GitLab's core values and how do they guide daily work?",
    "What are the key guidelines for working remotely at GitLab?",
    "How does GitLab approach communication and what are the norms?",
    "What is the handbook-first approach and why does GitLab use it?",
    "How do I get help when I'm stuck or have a question at GitLab?",
]


def get_current_question(step: int) -> str | None:
    """Return the onboarding question at the given step (0-indexed).

    - Returns None for step >= 5 (onboarding complete).
    - Clamps negative steps to 0 (returns question 0).
    - Never raises.
    """
    if step >= len(ONBOARDING_QUESTIONS):
        return None
    clamped = max(0, step)
    return ONBOARDING_QUESTIONS[clamped]
