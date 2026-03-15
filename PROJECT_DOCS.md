# Project Documentation — GitLab Guide Chatbot

## 1. Project Overview

**GitLab Guide** is a Generative AI chatbot that provides an interactive way to explore GitLab's publicly available Handbook and Product Direction pages. Inspired by GitLab's "build in public" philosophy, this project makes their extensive knowledge base accessible through natural conversation.

The chatbot uses **Retrieval-Augmented Generation (RAG)** to ground its responses in actual GitLab content, reducing hallucinations and providing source-backed answers. It also includes a suite of advanced UX, personalization, safety, and accessibility features designed for enterprise and onboarding use cases.

---

## 2. Approach & Architecture

### 2.1 Why RAG?

A pure LLM approach (without retrieval) would rely on the model's training data, which may be outdated or incomplete regarding GitLab-specific information. RAG solves this by:

1. **Indexing** GitLab's content into a searchable vector database
2. **Retrieving** the most relevant passages for each user question
3. **Generating** an answer grounded only in the retrieved context

This ensures answers are accurate, current (as of the last scrape), and verifiable through source citations.

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA PIPELINE                               │
│                                                                      │
│  GitLab Pages ──▶ Scraper ──▶ Chunker ──▶ FAISS Index               │
│  (HTML)           (BS4)       (LangChain) (Embeddings)               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                               │
│                                                                      │
│  User Query ──▶ Role Context ──▶ FAISS Search ──▶ Top-K Chunks      │
│                 + Language                                           │
│                                                    │                │
│                              Context + Query ◀─────┘                │
│                                    │                                │
│                                    ▼                                │
│                              Google Gemini                          │
│                         (Answer + Sources + Follow-ups)             │
│                                    │                                │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Streamlit UI Layer                        │   │
│  │  Sensitive Flagging │ Bookmarks │ Feedback │ Onboarding      │   │
│  │  Topic Clustering   │ i18n      │ Export   │ Empty State     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Scraper** | `requests` + `BeautifulSoup` | Crawl and extract content from GitLab pages |
| **Text Splitter** | LangChain `RecursiveCharacterTextSplitter` | Break documents into semantically coherent chunks |
| **Embeddings** | `all-MiniLM-L6-v2` (Sentence Transformers) | Convert text to 384-dim vectors for similarity search |
| **Vector Store** | FAISS | Fast approximate nearest-neighbor search |
| **LLM** | Google Gemini 2.0 Flash | Generate natural language answers from context |
| **Chat Chain** | LangChain `ConversationalRetrievalChain` | Orchestrate retrieval + generation with memory |
| **UI** | Streamlit | Interactive chat interface |
| **Topic Clustering** | `clustering.py` | URL-prefix-based cluster mapping for browse-by-category |
| **Follow-up Generator** | `follow_up.py` | Secondary Gemini call to produce 2–3 follow-up questions |
| **Sensitive Detector** | `sensitive.py` | Keyword + URL-path classification for HR/legal topics |
| **Export Service** | `export.py` | Serialize bookmarks to Markdown or PDF via `fpdf2` |
| **Onboarding Flow** | `onboarding.py` | Five-step guided tour for new hires |
| **i18n** | `i18n.py` | Translation dictionary for 5 languages with English fallback |
| **Feedback Store** | `feedback.py` | Session-scoped thumbs-up/down ratings with JSON export |

---

## 3. Key Technical Decisions

### 3.1 Google Gemini (Free Tier) over OpenAI

- **Cost**: Gemini 2.0 Flash offers a generous free tier, making the project accessible without paid API access
- **Quality**: Flash model provides strong instruction-following and reasoning for this use case
- **Trade-off**: Slightly less refined than GPT-4, but more than sufficient for handbook Q&A

### 3.2 FAISS over ChromaDB

- **Zero dependencies**: FAISS is a single `pip install` with no background services
- **Speed**: Excellent performance for our index size (~5,000–10,000 chunks)
- **Portability**: The index is a simple file pair, easy to deploy
- **Trade-off**: No built-in metadata filtering (handled in post-processing)

### 3.3 Sentence Transformers over API Embeddings

- **Offline**: No API calls needed for embedding, reducing latency and cost
- **Privacy**: Document content stays local during indexing
- **Quality**: `all-MiniLM-L6-v2` is a well-established model for semantic search

### 3.4 Streamlit over React/Gradio

- **Speed**: Fastest path from prototype to deployed app in Python
- **Built-in chat**: `st.chat_message` and `st.chat_input` provide native chat UX
- **Deployment**: Free hosting on Streamlit Community Cloud
- **Trade-off**: Less customizable than React, but sufficient for this use case

### 3.5 Session-Scoped State over Persistent Storage

All advanced feature data (bookmarks, feedback, search history, role profile, onboarding flags) lives in `st.session_state`. This keeps the app stateless and deployable without a database, while still providing a rich in-session experience. Users can export their data (bookmarks as PDF/Markdown, feedback as JSON) before the session ends.

### 3.6 Stateless Feature Modules

Each feature module (`clustering.py`, `follow_up.py`, etc.) exposes pure functions with no Streamlit imports. This makes them independently testable and reusable outside the Streamlit context.

---

## 4. Data Processing Details

### 4.1 Scraping Strategy

- **BFS Crawl**: Starting from seed URLs, discovers linked pages within the same domain prefix
- **Content Extraction**: Removes navigation, footers, sidebars, and scripts; preserves headings and body text
- **Polite Scraping**: 1-second delay between requests, custom User-Agent identifying the bot
- **Safety Cap**: Maximum 120 pages total to prevent runaway crawling

### 4.2 Chunking Strategy

- **Method**: `RecursiveCharacterTextSplitter` with separators `["\n\n", "\n", ". ", " ", ""]`
- **Chunk Size**: 1,000 characters (balances context richness with retrieval precision)
- **Overlap**: 200 characters (ensures no information is lost at chunk boundaries)
- **Metadata**: Each chunk retains its source URL and page title for citations

### 4.3 Retrieval Configuration

- **Search Type**: Cosine similarity (normalized embeddings)
- **Top-K**: 4 chunks per query (provides sufficient context without noise)
- **Memory**: Sliding window of 5 conversation turns (`ConversationBufferWindowMemory`)

### 4.4 Topic Cluster Mapping

Handbook URLs are mapped to named clusters using longest-prefix-first matching:

| URL Prefix | Cluster |
|---|---|
| `/handbook/engineering/` | Engineering |
| `/handbook/product/` | Engineering |
| `/handbook/company/culture/all-remote/` | Remote Work |
| `/handbook/company/culture/` | Culture |
| `/handbook/values/` | Culture |
| `/handbook/finance/` | Finance |
| `/handbook/total-rewards/` | Finance |
| `/handbook/people-group/` | People Ops |
| `/handbook/hiring/` | People Ops |
| `/handbook/security/` | Security |
| `/handbook/legal/` | Security |
| *(no match)* | General |

---

## 5. Advanced Features

### 5.1 Semantic Topic Clustering

Users can browse handbook topics by category before typing a question. Selecting a cluster pre-populates the chat input with a representative starter question and filters the "Try asking" sidebar examples to that cluster.

### 5.2 Conversation Memory

The chatbot retains the last 5 conversation turns using `ConversationBufferWindowMemory`. Follow-up questions that reference pronouns or implicit subjects from prior turns are resolved using the stored history.

### 5.3 Suggested Follow-Up Questions

After every answer, a secondary Gemini call generates 2–3 curiosity-driven follow-up questions. These are rendered as clickable buttons below the answer. If the LLM call fails, suggestions are silently omitted.

### 5.4 Bookmarking & Export

Users can star any assistant answer with a ⭐ toggle button. Bookmarked question-answer pairs (with source URLs) can be exported as:
- **Markdown** (`.md`) — plain text, suitable for note-taking tools
- **PDF** (`.pdf`) — formatted document via `fpdf2`, with fallback to Markdown bytes on failure

### 5.5 Sensitive Topic Flagging

Queries touching compensation, salary, equity, legal, termination, harassment, medical leave, or similar topics trigger a styled warning box prepended to the answer, advising the user to verify with HR/People Ops or Legal. Detection uses both keyword matching (whole-word regex) and source URL path inspection.

### 5.6 Onboarding Mode

On first load, new users are offered a guided 5-step tour covering:
1. GitLab's core values
2. Remote work guidelines
3. Communication norms
4. The handbook-first approach
5. How to get help

Each step is answered by the RAG pipeline. Users can ask follow-up questions between steps or skip the tour at any time.

### 5.7 Role-Based Personalization

Users select their role (Engineer, Designer, Product Manager, Sales, People Ops, Finance, Marketing) on first load. The selected role is injected into the LLM system prompt to bias answers toward role-relevant handbook sections. The role can be changed at any time via the sidebar selector.

### 5.8 Search History & Smart Suggestions

- **Recent Questions**: The sidebar shows the last 10 questions asked in the session. Clicking re-submits the question.
- **People Also Asked**: A curated list of 8 trending GitLab handbook questions is always visible in the sidebar.

### 5.9 Feedback Loop

Every assistant answer has 👍 / 👎 buttons. Ratings are stored in session state with the question, answer, timestamp, and source URLs. A thumbs-down reveals an optional comment field. All feedback can be downloaded as a JSON file from the sidebar.

### 5.10 Accessibility & Internationalization

- **Font size controls**: Small (14px), Medium (16px, default), Large (20px) — applied via injected CSS without page reload
- **Language support**: English, French, Spanish, German, Japanese — all static UI labels are translated via `i18n.py`; non-English selections append a language instruction to the LLM prompt
- **Keyboard navigation**: All interactive controls follow standard browser tab-order behavior

### 5.11 Empty State Design

When the chat is fresh (after role selection and onboarding), the main area shows example prompts grouped into four categories — Values & Culture, Engineering, Remote Work, People & Hiring — as clickable cards styled with GitLab orange accents.

---

## 6. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| GitLab pages have complex HTML with multiple content areas | Tried multiple CSS selectors (`main`, `article`, content divs) with fallbacks |
| Some pages are very short or navigation-only | Minimum content length filter (100 chars) skips low-value pages |
| LLM may hallucinate beyond retrieved context | Custom prompt explicitly instructs the model to answer only from provided context |
| Conversation context gets too long | Sliding window memory (5 turns) keeps context manageable |
| FAISS serialization security warning | Explicitly enabled `allow_dangerous_deserialization` since we control the index source |
| PDF generation may fail on non-Latin characters | `bookmarks_to_pdf` catches all `fpdf2` exceptions and falls back to Markdown bytes |
| Sensitive topic detection must not over-trigger | Single-word keywords use whole-word regex (`\bpip\b`) to avoid matching "pipeline" |
| Follow-up generation adds latency | Secondary LLM call is made after the main answer is already rendered; failures are silent |
| Streamlit re-renders on every interaction | All mutable state stored in `st.session_state`; `_init_session_state()` guards all keys |

---

## 7. Module Reference

| File | Responsibility |
|------|---------------|
| `app.py` | Streamlit UI, session state, all feature wiring |
| `chatbot.py` | `GitLabChatbot` class — RAG chain, memory, `ask()` |
| `scraper.py` | BFS web scraper for GitLab pages |
| `data_processor.py` | Text chunking + FAISS index builder |
| `config.py` | Centralized configuration constants |
| `clustering.py` | URL-to-cluster mapping, cluster questions |
| `follow_up.py` | Follow-up question generation via Gemini |
| `sensitive.py` | Sensitive topic detection + disclaimer HTML |
| `export.py` | Bookmark serialization to Markdown / PDF |
| `onboarding.py` | Five-step onboarding question sequence |
| `i18n.py` | Translation dictionary + `t(key, lang)` lookup |
| `feedback.py` | Feedback record management + JSON export |

---

## 8. Future Improvements

- **Scheduled re-scraping** to keep content fresh automatically
- **Hybrid search** (BM25 + semantic) for better retrieval accuracy
- **Streaming responses** using Gemini's streaming API for faster perceived response time
- **Persistent storage** (SQLite or Supabase) to retain bookmarks and feedback across sessions
- **Expanded data sources** (GitLab blog posts, release notes, community forums)
- **Analytics dashboard** aggregating feedback ratings across users
- **Additional languages** beyond the current five
