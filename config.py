"""
Centralized configuration for the GitLab GenAI Chatbot.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM Settings ──────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = "gemini-3-flash-preview"
LLM_TEMPERATURE = 0.3

# ── Embedding Settings ────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── Chunking Settings ─────────────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ── Retriever Settings ────────────────────────────────────────────────────────
RETRIEVER_K = 4

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")

# ── Scraper Settings ──────────────────────────────────────────────────────────
REQUEST_DELAY = 0.2  # seconds between requests
MAX_HANDBOOK_PAGES = 200
MAX_DIRECTION_PAGES = 400

# Seed URLs for the scraper
HANDBOOK_SEED_URLS = [
    "https://handbook.gitlab.com/handbook/",
    "https://handbook.gitlab.com/handbook/values/",
    "https://handbook.gitlab.com/handbook/communication/",
    "https://handbook.gitlab.com/handbook/leadership/",
    "https://handbook.gitlab.com/handbook/people-group/",
    "https://handbook.gitlab.com/handbook/people-group/employment-branding/",
    "https://handbook.gitlab.com/handbook/hiring/",
    "https://handbook.gitlab.com/handbook/hiring/interviewing/",
    "https://handbook.gitlab.com/handbook/total-rewards/",
    "https://handbook.gitlab.com/handbook/total-rewards/compensation/",
    "https://handbook.gitlab.com/handbook/engineering/",
    "https://handbook.gitlab.com/handbook/engineering/development/",
    "https://handbook.gitlab.com/handbook/engineering/infrastructure/",
    "https://handbook.gitlab.com/handbook/engineering/quality/",
    "https://handbook.gitlab.com/handbook/product/",
    "https://handbook.gitlab.com/handbook/product/product-manager-role/",
    "https://handbook.gitlab.com/handbook/product/ux/",
    "https://handbook.gitlab.com/handbook/marketing/",
    "https://handbook.gitlab.com/handbook/sales/",
    "https://handbook.gitlab.com/handbook/finance/",
    "https://handbook.gitlab.com/handbook/security/",
    "https://handbook.gitlab.com/handbook/legal/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/guide/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/getting-started/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/tips/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/management/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/meetings/",
    "https://handbook.gitlab.com/handbook/company/team-structure/",
    "https://handbook.gitlab.com/handbook/company/okrs/",
    "https://handbook.gitlab.com/handbook/company/strategy/",
    "https://handbook.gitlab.com/handbook/tools-and-tips/",
    "https://handbook.gitlab.com/handbook/support/",
    "https://handbook.gitlab.com/handbook/git-page-update/",
    "https://handbook.gitlab.com/handbook/on-call/",
    "https://handbook.gitlab.com/handbook/incentives/",
]

DIRECTION_SEED_URLS = [
    "https://about.gitlab.com/direction/",
    "https://about.gitlab.com/direction/plan/",
    "https://about.gitlab.com/direction/create/",
    "https://about.gitlab.com/direction/verify/",
    "https://about.gitlab.com/direction/package/",
    "https://about.gitlab.com/direction/deploy/",
    "https://about.gitlab.com/direction/secure/",
    "https://about.gitlab.com/direction/govern/",
    "https://about.gitlab.com/direction/monitor/",
    "https://about.gitlab.com/direction/manage/",
    "https://about.gitlab.com/direction/modelops/",
    "https://about.gitlab.com/direction/enablement/",
    "https://about.gitlab.com/direction/saas-platforms/",
]
