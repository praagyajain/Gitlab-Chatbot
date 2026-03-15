"""
Follow-up question generator for the GitLab Guide chatbot.

Uses a secondary LLM call to produce 2-3 curiosity-driven follow-up
questions based on a given answer.
"""

from langchain_google_genai import ChatGoogleGenerativeAI

_PROMPT_TEMPLATE = (
    "Based on the following answer, generate exactly 2 to 3 short, distinct, "
    "curiosity-driven follow-up questions a reader might want to ask next. "
    "Output only the questions, one per line, numbered (e.g. '1. ...').\n\n"
    "Answer:\n{answer}\n\nFollow-up questions:"
)


def generate_follow_ups(answer: str, llm: ChatGoogleGenerativeAI) -> list[str]:
    """
    Return 2-3 follow-up question strings derived from *answer*.

    Returns an empty list on any failure or if the parsed result is not
    between 2 and 3 items — never raises.
    """
    try:
        prompt = _PROMPT_TEMPLATE.format(answer=answer)
        response = llm.invoke(prompt)

        # Extract text content from the response
        raw_text = response.content if hasattr(response, "content") else str(response)

        questions = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip leading numbering/bullets: "1.", "1)", "-", "*", "•"
            for prefix_chars in ("1.", "2.", "3.", "4.", "5.", "1)", "2)", "3)"):
                if line.startswith(prefix_chars):
                    line = line[len(prefix_chars):].strip()
                    break
            else:
                # Strip single bullet characters
                if line and line[0] in ("-", "*", "•"):
                    line = line[1:].strip()

            if line:
                questions.append(line)

        if len(questions) < 2 or len(questions) > 3:
            return []

        return questions

    except Exception:
        return []
