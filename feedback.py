"""Feedback store utilities for the GitLab Guide chatbot."""

import json
from datetime import datetime, timezone


def record_feedback(
    session_state,
    question: str,
    answer: str,
    rating: str,
    sources: list[dict],
    comment: str = "",
) -> None:
    """Append or update a feedback record in session_state.feedback.

    If a record matching (question, answer) already exists, it is updated
    in place (rating, timestamp, comment). Otherwise a new record is appended.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    for record in session_state.feedback:
        if record["question"] == question and record["answer"] == answer:
            record["rating"] = rating
            record["timestamp"] = timestamp
            record["comment"] = comment
            return

    session_state.feedback.append(
        {
            "question": question,
            "answer": answer,
            "rating": rating,
            "timestamp": timestamp,
            "sources": sources,
            "comment": comment,
        }
    )


def feedback_to_json(feedback: list[dict]) -> str:
    """Serialize feedback list to a pretty-printed JSON string."""
    return json.dumps(feedback, indent=2)
