"""Semantic topic clustering for handbook URLs."""

# Maps URL prefix -> cluster name. Order matters for longest-prefix-first matching.
CLUSTER_PREFIXES: dict[str, str] = {
    "/handbook/company/culture/all-remote/": "Remote Work",
    "/handbook/company/culture/": "Culture",
    "/handbook/engineering/": "Engineering",
    "/handbook/product/": "Engineering",
    "/handbook/values/": "Culture",
    "/handbook/finance/": "Finance",
    "/handbook/total-rewards/": "Finance",
    "/handbook/people-group/": "People Ops",
    "/handbook/hiring/": "People Ops",
    "/handbook/security/": "Security",
    "/handbook/legal/": "Security",
}

CLUSTER_QUESTIONS: dict[str, list[str]] = {
    "Engineering": [
        "What is GitLab's engineering workflow and development process?",
        "How does GitLab handle code review and merge requests?",
        "What are the engineering career levels and expectations at GitLab?",
    ],
    "Culture": [
        "What are GitLab's core values and how do they guide daily work?",
        "How does GitLab foster an inclusive and diverse culture?",
        "What is the handbook-first approach and why does GitLab use it?",
    ],
    "Remote Work": [
        "What are the key guidelines for working remotely at GitLab?",
        "How does GitLab support work-life balance for remote employees?",
        "What tools and practices does GitLab use for async communication?",
    ],
    "Finance": [
        "How does GitLab handle expense reimbursement?",
        "What is GitLab's approach to equity and compensation?",
        "How does the annual planning and budgeting process work at GitLab?",
    ],
    "People Ops": [
        "How does the onboarding process work for new GitLab team members?",
        "What are the leave policies at GitLab?",
        "How does GitLab handle performance reviews and feedback?",
    ],
    "Security": [
        "What are GitLab's security policies and best practices?",
        "How does GitLab handle data privacy and compliance?",
        "What should I do if I discover a security vulnerability?",
    ],
    "General": [
        "How do I get help when I'm stuck or have a question at GitLab?",
        "How does GitLab approach communication and what are the norms?",
        "Where can I find information about GitLab's products and services?",
    ],
}

VALID_CLUSTERS: frozenset[str] = frozenset(CLUSTER_QUESTIONS.keys())


def get_cluster(url: str) -> str:
    """Return cluster name for a URL, matching longest prefix first, defaulting to 'General'."""
    for prefix, cluster in CLUSTER_PREFIXES.items():
        if url.startswith(prefix):
            return cluster
    return "General"


def get_starter_question(cluster: str) -> str:
    """Return the first question from CLUSTER_QUESTIONS for the cluster."""
    questions = CLUSTER_QUESTIONS.get(cluster, CLUSTER_QUESTIONS["General"])
    return questions[0]


def get_cluster_questions(cluster: str) -> list[str]:
    """Return all questions for the cluster."""
    return CLUSTER_QUESTIONS.get(cluster, CLUSTER_QUESTIONS["General"])
