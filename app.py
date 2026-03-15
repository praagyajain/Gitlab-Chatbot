"""
GitLab Guide — A GenAI Chatbot for GitLab Handbook & Direction

Streamlit-based chat interface with dark theme, source citations,
conversational memory, topic clustering, onboarding, role personalization,
i18n, bookmarks, feedback, and more.

Usage:
    streamlit run app.py
"""

import streamlit as st
from chatbot import GitLabChatbot
from clustering import (
    CLUSTER_QUESTIONS,
    get_cluster_questions,
    get_starter_question,
)
from follow_up import generate_follow_ups
from sensitive import is_sensitive, DISCLAIMER_HTML
from export import bookmarks_to_markdown, bookmarks_to_pdf
from onboarding import get_current_question
from i18n import t, SUPPORTED_LANGUAGES
from feedback import record_feedback, feedback_to_json

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitLab Guide — AI Chatbot",
    page_icon="🦊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Global overrides ─────────────────────────────────────── */
.stApp {
    background: linear-gradient(165deg, #0F0F23 0%, #13132B 50%, #1A1A2E 100%);
}

/* ── Header / Hero ────────────────────────────────────────── */
.hero-container {
    text-align: center;
    padding: 1.5rem 0 1rem;
    margin-bottom: 0.5rem;
}
.hero-emoji {
    font-size: 3rem;
    margin-bottom: 0.25rem;
    animation: bounce 2s ease infinite;
}
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}
.hero-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #FC6D26 0%, #E24329 40%, #FCA326 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}
.hero-subtitle {
    color: rgba(232, 232, 240, 0.6);
    font-size: 0.95rem;
    font-weight: 300;
    margin-top: 0.25rem;
}

/* ── Chat messages ────────────────────────────────────────── */
.stChatMessage {
    border-radius: 16px !important;
    border: 1px solid rgba(252, 109, 38, 0.08) !important;
    backdrop-filter: blur(10px);
    margin-bottom: 0.75rem !important;
}
[data-testid="stChatMessageContent"] {
    font-size: 0.95rem;
    line-height: 1.65;
}

/* ── Source pills ─────────────────────────────────────────── */
.source-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(252, 109, 38, 0.15);
}
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.75rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(252, 109, 38, 0.12), rgba(226, 67, 41, 0.08));
    border: 1px solid rgba(252, 109, 38, 0.2);
    font-size: 0.78rem;
    color: #FCA326;
    text-decoration: none;
    transition: all 0.25s ease;
}
.source-pill:hover {
    background: linear-gradient(135deg, rgba(252, 109, 38, 0.25), rgba(226, 67, 41, 0.18));
    border-color: rgba(252, 109, 38, 0.45);
    transform: translateY(-1px);
    color: #FC6D26;
}

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0D1F 0%, #141428 100%) !important;
    border-right: 1px solid rgba(252, 109, 38, 0.1) !important;
}
.sidebar-brand {
    text-align: center;
    padding: 1rem 0.5rem 1.25rem;
    border-bottom: 1px solid rgba(252, 109, 38, 0.1);
    margin-bottom: 1.25rem;
}
.sidebar-brand h2 {
    font-size: 1.15rem;
    font-weight: 600;
    color: #E8E8F0;
    margin: 0.25rem 0 0;
}
.sidebar-brand p {
    font-size: 0.78rem;
    color: rgba(232, 232, 240, 0.45);
    margin: 0.15rem 0 0;
}
.sidebar-section-title {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(252, 109, 38, 0.6);
    margin-bottom: 0.5rem;
}

/* ── Quick-action buttons ─────────────────────────────────── */
.stButton > button {
    width: 100%;
    text-align: left;
    padding: 0.6rem 0.85rem;
    border-radius: 10px;
    border: 1px solid rgba(252, 109, 38, 0.12);
    background: rgba(26, 26, 46, 0.6);
    color: #E8E8F0;
    font-size: 0.82rem;
    font-weight: 400;
    transition: all 0.2s ease;
    margin-bottom: 0.25rem;
}
.stButton > button:hover {
    border-color: rgba(252, 109, 38, 0.4);
    background: rgba(252, 109, 38, 0.08);
    transform: translateX(3px);
}

/* ── Chat input ───────────────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    border-radius: 14px !important;
    border: 1px solid rgba(252, 109, 38, 0.2) !important;
    background: rgba(26, 26, 46, 0.8) !important;
    font-size: 0.92rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: rgba(252, 109, 38, 0.5) !important;
    box-shadow: 0 0 0 2px rgba(252, 109, 38, 0.1) !important;
}

/* ── Status / info boxes ──────────────────────────────────── */
.status-box {
    background: linear-gradient(135deg, rgba(252, 109, 38, 0.06), rgba(252, 163, 38, 0.04));
    border: 1px solid rgba(252, 109, 38, 0.15);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    color: rgba(232, 232, 240, 0.8);
    line-height: 1.6;
}

/* ── Empty state cards ────────────────────────────────────── */
.empty-state-card {
    background: rgba(26, 26, 46, 0.7);
    border: 1px solid rgba(252, 109, 38, 0.18);
    border-radius: 14px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.85rem;
    color: #E8E8F0;
}
.empty-state-card:hover {
    border-color: rgba(252, 109, 38, 0.5);
    background: rgba(252, 109, 38, 0.08);
}
.empty-state-category {
    font-size: 0.78rem;
    font-weight: 600;
    color: #FC6D26;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.5rem;
    margin-top: 1rem;
}

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(252, 109, 38, 0.2);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(252, 109, 38, 0.35); }

/* ── Footer ───────────────────────────────────────────────── */
.footer {
    text-align: center;
    font-size: 0.72rem;
    color: rgba(232, 232, 240, 0.3);
    padding: 1.5rem 0 0.5rem;
    border-top: 1px solid rgba(252, 109, 38, 0.06);
    margin-top: 2rem;
}
.footer a { color: rgba(252, 109, 38, 0.5); text-decoration: none; }
.footer a:hover { color: #FC6D26; }
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ──────────────────────────────────────────────
def _init_session_state():
    """Initialize all session state keys with their default values."""
    defaults = {
        "messages": [],
        "chatbot": None,
        "initialized": False,
        "bookmarks": [],
        "feedback": [],
        "search_history": [],
        "role_profile": None,
        "role_selected": False,
        "onboarding_complete": False,
        "onboarding_step": 0,
        "font_size": "medium",
        "language": "English",
        "selected_cluster": None,
        "rated_messages": set(),
        "pending_question": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

_init_session_state()

# ── Constants ─────────────────────────────────────────────────────────────────
PEOPLE_ALSO_ASKED = [
    "What are GitLab's core values?",
    "How does GitLab handle remote work?",
    "What is the handbook-first approach?",
    "How does GitLab approach async communication?",
    "What are GitLab's engineering career levels?",
    "How does GitLab handle performance reviews?",
    "What is GitLab's approach to diversity and inclusion?",
    "How does GitLab's product direction work?",
]

ROLE_OPTIONS = [
    "Engineer",
    "Designer",
    "Product Manager",
    "Sales",
    "People Ops",
    "Finance",
    "Marketing",
    "Other / Skip",
]

FONT_SIZE_MAP = {
    "Small": "14px",
    "Medium": "16px",
    "Large": "20px",
}

EMPTY_STATE_CATEGORIES = {
    "Values & Culture": [
        "What are GitLab's core values?",
        "How does GitLab foster inclusion?",
        "What is the handbook-first approach?",
    ],
    "Engineering": [
        "What is GitLab's engineering workflow?",
        "How does code review work at GitLab?",
        "What are engineering career levels?",
    ],
    "Remote Work": [
        "What are GitLab's remote work guidelines?",
        "How does GitLab handle async communication?",
        "What tools does GitLab use for remote work?",
    ],
    "People & Hiring": [
        "How does GitLab's hiring process work?",
        "What are GitLab's leave policies?",
        "How does onboarding work at GitLab?",
    ],
}

CLUSTER_NAMES = list(CLUSTER_QUESTIONS.keys())

# ── Helper: get LLM from chatbot ──────────────────────────────────────────────
def _get_llm():
    """Safely retrieve the LLM instance from the chatbot chain."""
    try:
        return st.session_state.chatbot.chain.combine_docs_chain.llm_chain.llm
    except AttributeError:
        return None


# ── Helper: build role context string ────────────────────────────────────────
def _build_role_context() -> str:
    role = st.session_state.role_profile
    lang = st.session_state.language
    parts = []
    if role:
        parts.append(
            f"The user is a {role}. Prioritize {role}-specific handbook sections."
        )
    if lang != "English":
        parts.append(f"Please respond in {lang}.")
    return " ".join(parts)


# ── Helper: bookmark toggle ───────────────────────────────────────────────────
def _toggle_bookmark(msg_index: int, question: str, answer: str, sources: list):
    existing = [b for b in st.session_state.bookmarks if b["message_index"] == msg_index]
    if existing:
        st.session_state.bookmarks = [
            b for b in st.session_state.bookmarks if b["message_index"] != msg_index
        ]
    else:
        st.session_state.bookmarks.append({
            "question": question,
            "answer": answer,
            "sources": sources,
            "message_index": msg_index,
        })


# ── Sidebar ───────────────────────────────────────────────────────────────────
lang = st.session_state.language

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <div style="font-size: 2.5rem;">🦊</div>
        <h2>{t('sidebar_title', lang)}</h2>
        <p>AI-Powered Handbook Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Task 19: Font size & language selectors ───────────────────────────────
    st.markdown(f'<div class="sidebar-section-title">⚙️ {t("font_size_label", lang)}</div>', unsafe_allow_html=True)
    font_choice = st.selectbox(
        t("font_size_label", lang),
        options=["Small", "Medium", "Large"],
        index=["Small", "Medium", "Large"].index(
            {"small": "Small", "medium": "Medium", "large": "Large"}.get(
                st.session_state.font_size, "Medium"
            )
        ),
        label_visibility="collapsed",
        key="font_size_select",
    )
    st.session_state.font_size = font_choice.lower()

    st.markdown(f'<div class="sidebar-section-title">🌐 {t("language_label", lang)}</div>', unsafe_allow_html=True)
    lang_choice = st.selectbox(
        t("language_label", lang),
        options=SUPPORTED_LANGUAGES,
        index=SUPPORTED_LANGUAGES.index(st.session_state.language),
        label_visibility="collapsed",
        key="language_select",
    )
    if lang_choice != st.session_state.language:
        st.session_state.language = lang_choice
        st.rerun()
    lang = st.session_state.language

    # ── Task 18: Role selector in sidebar ────────────────────────────────────
    st.markdown(f'<div class="sidebar-section-title">👤 {t("role_label", lang)}</div>', unsafe_allow_html=True)
    current_role = st.session_state.role_profile or "Other / Skip"
    role_idx = ROLE_OPTIONS.index(current_role) if current_role in ROLE_OPTIONS else len(ROLE_OPTIONS) - 1
    sidebar_role = st.selectbox(
        t("role_label", lang),
        options=ROLE_OPTIONS,
        index=role_idx,
        label_visibility="collapsed",
        key="sidebar_role_select",
    )
    if sidebar_role != current_role:
        st.session_state.role_profile = None if sidebar_role == "Other / Skip" else sidebar_role
        st.session_state.role_selected = True
        st.rerun()

    st.markdown("---")

    # ── Task 11: Browse by Topic ──────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-title">🗂️ Browse by Topic</div>', unsafe_allow_html=True)
    for cluster_name in CLUSTER_NAMES:
        active = st.session_state.selected_cluster == cluster_name
        label = f"{'✅' if active else '→'} {cluster_name}"
        if st.button(label, key=f"cluster_{cluster_name}"):
            st.session_state.selected_cluster = cluster_name
            st.session_state.pending_question = get_starter_question(cluster_name)
            st.rerun()
    if st.session_state.selected_cluster:
        if st.button("✖ Clear Topic Filter", key="clear_cluster"):
            st.session_state.selected_cluster = None
            st.rerun()

    st.markdown("---")

    # ── Task 11: Try asking (filtered by cluster) ─────────────────────────────
    st.markdown(f'<div class="sidebar-section-title">💡 {t("try_asking", lang)}</div>', unsafe_allow_html=True)
    if st.session_state.selected_cluster:
        example_questions = get_cluster_questions(st.session_state.selected_cluster)
    else:
        example_questions = [
            "What are GitLab's core values?",
            "How does GitLab approach remote work?",
            "What is GitLab's product direction for CI/CD?",
            "How does GitLab handle hiring and interviews?",
            "What is GitLab's communication style?",
            "Tell me about GitLab's engineering culture",
            "What are GitLab's OKRs?",
            "How does GitLab approach security?",
        ]
    for q in example_questions:
        if st.button(f"→ {q}", key=f"ex_{hash(q)}"):
            st.session_state.pending_question = q
            st.rerun()

    st.markdown("---")

    # ── Task 12: Recent Questions ─────────────────────────────────────────────
    if st.session_state.search_history:
        st.markdown(f'<div class="sidebar-section-title">🕐 {t("recent_questions", lang)}</div>', unsafe_allow_html=True)
        recent = st.session_state.search_history[-10:][::-1]
        for rq in recent:
            short = rq[:55] + "…" if len(rq) > 55 else rq
            if st.button(f"↩ {short}", key=f"hist_{hash(rq)}"):
                st.session_state.pending_question = rq
                st.rerun()
        st.markdown("---")

    # ── Task 12: People also asked ────────────────────────────────────────────
    st.markdown(f'<div class="sidebar-section-title">🔥 {t("people_also_asked", lang)}</div>', unsafe_allow_html=True)
    for pq in PEOPLE_ALSO_ASKED:
        short = pq[:55] + "…" if len(pq) > 55 else pq
        if st.button(f"→ {short}", key=f"paa_{hash(pq)}"):
            st.session_state.pending_question = pq
            st.rerun()

    st.markdown("---")

    # ── Task 15: Bookmarks & Export ───────────────────────────────────────────
    bm_count = len(st.session_state.bookmarks)
    st.markdown(
        f'<div class="sidebar-section-title">⭐ {t("bookmarks", lang)} ({bm_count})</div>',
        unsafe_allow_html=True,
    )
    if bm_count > 0:
        md_bytes = bookmarks_to_markdown(st.session_state.bookmarks).encode("utf-8")
        st.download_button(
            label=t("export_markdown", lang),
            data=md_bytes,
            file_name="gitlab_notes.md",
            mime="text/markdown",
            key="dl_md",
        )
        pdf_bytes = bookmarks_to_pdf(st.session_state.bookmarks)
        st.download_button(
            label=t("export_pdf", lang),
            data=pdf_bytes,
            file_name="gitlab_notes.pdf",
            mime="application/pdf",
            key="dl_pdf",
        )
    else:
        st.button(t("export_markdown", lang), key="dl_md_disabled", disabled=True)
        st.button(t("export_pdf", lang), key="dl_pdf_disabled", disabled=True)

    st.markdown("---")

    # ── Task 16: Download Feedback JSON ──────────────────────────────────────
    if st.session_state.feedback:
        fb_json = feedback_to_json(st.session_state.feedback).encode("utf-8")
        st.download_button(
            label="📥 Download Feedback JSON",
            data=fb_json,
            file_name="feedback.json",
            mime="application/json",
            key="dl_feedback",
        )

    st.markdown("---")

    # ── Task 12: Clear chat ───────────────────────────────────────────────────
    st.markdown(f'<div class="sidebar-section-title">⚙️ Controls</div>', unsafe_allow_html=True)
    if st.button(f"🗑️ {t('clear_chat', lang)}", key="clear_chat"):
        st.session_state.messages = []
        st.session_state.search_history = []
        if st.session_state.chatbot:
            st.session_state.chatbot.clear_memory()
        st.rerun()

    st.markdown("""
    <div style="font-size: 0.75rem; color: rgba(232,232,240,0.35); line-height: 1.5; padding: 0.5rem 0;">
        <strong style="color: rgba(252,109,38,0.5);">About</strong><br>
        This chatbot uses RAG (Retrieval-Augmented Generation) to answer questions
        from GitLab's Handbook and Direction pages.<br><br>
        Powered by Google Gemini &amp; LangChain
    </div>
    """, unsafe_allow_html=True)

# ── Task 19: Inject font-size CSS ────────────────────────────────────────────
font_px = FONT_SIZE_MAP.get(font_choice, "16px")
st.markdown(
    f"<style>[data-testid='stChatMessageContent'] {{ font-size: {font_px} !important; }}</style>",
    unsafe_allow_html=True,
)

# ── Main Content Area ─────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-emoji">🦊</div>
    <h1 class="hero-title">GitLab Guide</h1>
    <p class="hero-subtitle">Ask anything about GitLab's Handbook &amp; Product Direction</p>
</div>
""", unsafe_allow_html=True)


# ── Initialize Chatbot ────────────────────────────────────────────────────────
def init_chatbot():
    if st.session_state.chatbot is None:
        st.session_state.chatbot = GitLabChatbot()
    if not st.session_state.initialized:
        try:
            st.session_state.chatbot.initialize()
            st.session_state.initialized = True
        except (ValueError, FileNotFoundError) as e:
            return str(e)
    return None


init_error = init_chatbot()

if init_error:
    st.markdown(f"""
    <div class="status-box">
        ⚠️ <strong>Setup Required</strong><br><br>
        {init_error}<br><br>
        <strong>Quick Start:</strong><br>
        1. Copy <code>.env.example</code> to <code>.env</code><br>
        2. Add your <code>GOOGLE_API_KEY</code><br>
        3. Run <code>python scraper.py</code><br>
        4. Run <code>python data_processor.py</code><br>
        5. Restart with <code>streamlit run app.py</code>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Task 18: Role selection on very first load ────────────────────────────
    if not st.session_state.role_selected and not st.session_state.onboarding_complete:
        st.markdown("""
        <div class="status-box">
            👋 <strong>Welcome to GitLab Guide!</strong><br>
            Tell us your role so we can personalize your experience.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("**What is your role?**")
        cols = st.columns(4)
        for i, role_opt in enumerate(ROLE_OPTIONS):
            with cols[i % 4]:
                if st.button(role_opt, key=f"role_init_{role_opt}"):
                    st.session_state.role_profile = None if role_opt == "Other / Skip" else role_opt
                    st.session_state.role_selected = True
                    st.rerun()

    else:
        # ── Task 17: Onboarding banner / tour ─────────────────────────────────
        if not st.session_state.onboarding_complete:
            if st.session_state.onboarding_step == 0:
                # Show banner
                st.markdown(f"""
                <div class="status-box">
                    🎉 <strong>{t('onboarding_banner_title', lang)}</strong><br>
                    {t('onboarding_banner_body', lang)}
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🚀 {t('start_tour', lang)}", key="start_tour"):
                        st.session_state.onboarding_step = 1
                        st.rerun()
                with col2:
                    if st.button(f"⏭ {t('skip_tour', lang)}", key="skip_tour"):
                        st.session_state.onboarding_complete = True
                        st.rerun()
            else:
                # Active tour
                current_q = get_current_question(st.session_state.onboarding_step - 1)
                if current_q:
                    st.info(
                        f"**Tour Step {st.session_state.onboarding_step}/5:** {current_q}",
                        icon="🗺️",
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"▶ {t('next_question', lang)}", key="tour_next"):
                            st.session_state.onboarding_step += 1
                            if st.session_state.onboarding_step > 5:
                                st.session_state.onboarding_complete = True
                            st.rerun()
                    with col2:
                        if st.button(f"⏭ {t('skip_tour', lang)}", key="tour_skip"):
                            st.session_state.onboarding_complete = True
                            st.rerun()
                    # Auto-ask the tour question if not already in messages
                    last_user = next(
                        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
                        None,
                    )
                    if last_user != current_q:
                        st.session_state.pending_question = current_q
                        st.rerun()
                else:
                    st.session_state.onboarding_complete = True
                    st.rerun()

        # ── Task 20: Empty state panel ────────────────────────────────────────
        if not st.session_state.messages and (
            st.session_state.onboarding_complete or st.session_state.role_selected
        ):
            st.markdown("""
            <div style="text-align:center; padding: 1rem 0 0.5rem;">
                <span style="font-size:1.1rem; color: rgba(232,232,240,0.6);">
                    What would you like to explore today?
                </span>
            </div>
            """, unsafe_allow_html=True)
            for category, prompts in EMPTY_STATE_CATEGORIES.items():
                st.markdown(
                    f'<div class="empty-state-category">🔹 {category}</div>',
                    unsafe_allow_html=True,
                )
                for prompt_text in prompts:
                    if st.button(prompt_text, key=f"empty_{hash(prompt_text)}"):
                        st.session_state.pending_question = prompt_text
                        st.rerun()

        elif not st.session_state.messages:
            # Classic welcome box (pre-onboarding-complete, no role selected yet)
            st.markdown("""
            <div class="status-box">
                👋 <strong>Welcome!</strong> I'm your GitLab Guide — ask me anything about
                GitLab's Handbook, values, remote work culture, engineering practices,
                product direction, and more.<br><br>
                Try one of the example questions in the sidebar, or type your own below!
            </div>
            """, unsafe_allow_html=True)

        # ── Display chat history ───────────────────────────────────────────────
        for msg_idx, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(msg["content"], unsafe_allow_html=True)
            else:
                with st.chat_message("assistant", avatar="🦊"):
                    st.markdown(msg["content"], unsafe_allow_html=True)

                    # ── Task 15: Bookmark button ──────────────────────────────
                    raw_ans = msg.get("raw_answer", "")
                    sources = msg.get("sources", [])
                    # Find the preceding user message as the question
                    question_for_bm = ""
                    for prev in reversed(st.session_state.messages[:msg_idx]):
                        if prev["role"] == "user":
                            question_for_bm = prev["content"]
                            break

                    is_bookmarked = any(
                        b["message_index"] == msg_idx for b in st.session_state.bookmarks
                    )
                    bm_label = "⭐ Bookmarked" if is_bookmarked else "☆ Bookmark"
                    if st.button(bm_label, key=f"bm_{msg_idx}"):
                        _toggle_bookmark(msg_idx, question_for_bm, raw_ans, sources)
                        st.rerun()

                    # ── Task 13: Follow-up suggestions ────────────────────────
                    follow_ups = msg.get("follow_ups", [])
                    if follow_ups:
                        st.markdown(
                            "<div style='font-size:0.78rem; color: rgba(252,109,38,0.7); margin-top:0.5rem;'>💬 Follow-up suggestions:</div>",
                            unsafe_allow_html=True,
                        )
                        fu_cols = st.columns(len(follow_ups))
                        for fi, fu_q in enumerate(follow_ups):
                            with fu_cols[fi]:
                                if st.button(fu_q, key=f"fu_{msg_idx}_{fi}"):
                                    st.session_state.pending_question = fu_q
                                    st.rerun()

                    # ── Task 16: Feedback buttons ─────────────────────────────
                    already_rated = msg_idx in st.session_state.rated_messages
                    fb_col1, fb_col2 = st.columns([1, 1])
                    with fb_col1:
                        up_label = "👍 Helpful" if not already_rated else "👍"
                        if st.button(up_label, key=f"up_{msg_idx}"):
                            record_feedback(
                                st.session_state,
                                question=question_for_bm,
                                answer=raw_ans,
                                rating="up",
                                sources=sources,
                            )
                            st.session_state.rated_messages.add(msg_idx)
                            st.rerun()
                    with fb_col2:
                        down_label = "👎 Not helpful" if not already_rated else "👎"
                        if st.button(down_label, key=f"down_{msg_idx}"):
                            record_feedback(
                                st.session_state,
                                question=question_for_bm,
                                answer=raw_ans,
                                rating="down",
                                sources=sources,
                            )
                            st.session_state.rated_messages.add(msg_idx)
                            st.rerun()

                    # Show comment box after thumbs-down
                    if already_rated:
                        last_fb = next(
                            (
                                r for r in reversed(st.session_state.feedback)
                                if r["question"] == question_for_bm and r["answer"] == raw_ans
                            ),
                            None,
                        )
                        if last_fb and last_fb.get("rating") == "down":
                            comment = st.text_input(
                                t("feedback_prompt", lang),
                                key=f"fb_comment_{msg_idx}",
                                placeholder="Optional: what could be improved?",
                            )
                            if st.button("Submit feedback", key=f"fb_submit_{msg_idx}") and comment:
                                record_feedback(
                                    st.session_state,
                                    question=question_for_bm,
                                    answer=raw_ans,
                                    rating="down",
                                    sources=sources,
                                    comment=comment,
                                )
                                st.rerun()

        # ── Handle pending question / chat input ──────────────────────────────
        prompt = None
        if st.session_state.pending_question:
            prompt = st.session_state.pending_question
            st.session_state.pending_question = None

        user_input = st.chat_input("Ask about GitLab's Handbook or Direction...")
        if user_input:
            prompt = user_input

        if prompt:
            # ── Task 12: Append to search history ────────────────────────────
            st.session_state.search_history.append(prompt)

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🦊"):
                with st.spinner("Searching GitLab's knowledge base..."):
                    try:
                        role_context = _build_role_context()
                        result = st.session_state.chatbot.ask(prompt, role_context=role_context)
                        answer = result["answer"]
                        raw_answer = result["raw_answer"]
                        sources = result["sources"]
                        source_urls = [s["url"] for s in sources]

                        # ── Task 14: Sensitive topic disclaimer ───────────────
                        prefix_html = ""
                        if is_sensitive(prompt, source_urls):
                            prefix_html = DISCLAIMER_HTML

                        # Format sources as clickable pills
                        source_html = ""
                        if sources:
                            pills = ""
                            for s in sources[:4]:
                                title = s["title"][:50] + "..." if len(s["title"]) > 50 else s["title"]
                                pills += f'<a href="{s["url"]}" target="_blank" class="source-pill">📄 {title}</a>'
                            source_html = f'<div class="source-container">{pills}</div>'

                        full_response = f"{prefix_html}{answer}{source_html}"
                        st.markdown(full_response, unsafe_allow_html=True)

                        # ── Task 13: Generate follow-ups ──────────────────────
                        llm = _get_llm()
                        follow_ups = []
                        if llm:
                            follow_ups = generate_follow_ups(raw_answer, llm)

                        # Show follow-ups immediately after new answer
                        if follow_ups:
                            st.markdown(
                                "<div style='font-size:0.78rem; color: rgba(252,109,38,0.7); margin-top:0.5rem;'>💬 Follow-up suggestions:</div>",
                                unsafe_allow_html=True,
                            )
                            fu_cols = st.columns(len(follow_ups))
                            for fi, fu_q in enumerate(follow_ups):
                                with fu_cols[fi]:
                                    if st.button(fu_q, key=f"fu_new_{fi}"):
                                        st.session_state.pending_question = fu_q
                                        st.rerun()

                        new_msg_idx = len(st.session_state.messages)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response,
                            "raw_answer": raw_answer,
                            "sources": sources,
                            "message_index": new_msg_idx,
                            "follow_ups": follow_ups,
                        })

                    except Exception as e:
                        error_msg = (
                            f"😔 Sorry, I encountered an error: `{str(e)[:200]}`\n\n"
                            "Please try again or rephrase your question."
                        )
                        st.markdown(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "raw_answer": "",
                            "sources": [],
                            "message_index": len(st.session_state.messages),
                            "follow_ups": [],
                        })

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Built with ❤️ using
    <a href="https://streamlit.io" target="_blank">Streamlit</a>,
    <a href="https://langchain.com" target="_blank">LangChain</a>, and
    <a href="https://ai.google.dev" target="_blank">Google Gemini</a>
    &nbsp;·&nbsp; Data sourced from
    <a href="https://handbook.gitlab.com" target="_blank">GitLab Handbook</a>
</div>
""", unsafe_allow_html=True)
