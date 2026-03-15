# 🦊 GitLab Guide — GenAI Chatbot

An AI-powered chatbot that lets you explore **GitLab's Handbook** and **Product Direction** through natural conversation. Built with RAG (Retrieval-Augmented Generation), powered by Google Gemini, LangChain, and FAISS — with a full suite of advanced UX, personalization, and accessibility features.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-4285F4?logo=google&logoColor=white)

---

## ✨ Features

### Core
- **🔍 Intelligent Q&A** — Ask natural language questions about GitLab's handbook, values, engineering practices, remote work culture, and product direction
- **📄 Source Citations** — Every answer includes clickable links to the original GitLab pages
- **💬 Conversation Memory** — Follow-up questions retain context from the last 5 exchanges
- **🎨 Premium Dark UI** — GitLab-branded interface with smooth animations and responsive layout

### Advanced
- **🗂️ Topic Clustering** — Browse handbook topics by category (Engineering, Culture, Remote Work, Finance, People Ops, Security) before typing a question
- **💡 Suggested Follow-ups** — 2–3 smart follow-up questions surfaced after every answer
- **⭐ Bookmarking & Export** — Star useful answers and export your session as PDF or Markdown
- **⚠️ Sensitive Topic Flagging** — HR, compensation, and legal queries get an automatic disclaimer to verify with People Ops
- **🎓 Onboarding Mode** — Guided 5-step tour for new hires covering GitLab's core values, remote work, communication norms, handbook-first approach, and how to get help
- **👤 Role-Based Personalization** — Select your role (Engineer, Designer, Sales, etc.) to get tailored answers
- **🕐 Search History** — Sidebar shows your last 10 questions; click to re-ask
- **🔥 People Also Asked** — Curated trending questions always visible in the sidebar
- **👍 Feedback Loop** — Rate every answer with 👍/👎 and download session feedback as JSON
- **🌐 Multilingual Support** — English, French, Spanish, German, Japanese
- **🔤 Font Size Controls** — Small / Medium / Large text for accessibility
- **🖼️ Empty State Design** — Categorized example prompts when the chat is fresh

---

## 🏗️ Architecture

```
User Question
     │
     ▼
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Streamlit   │────▶│  FAISS Retriever  │────▶│  Google Gemini   │
│  Chat UI     │     │  (Top-K Chunks)   │     │  (Answer Gen)    │
│              │◀────│                   │◀────│                  │
└──────────────┘     └──────────────────┘     └─────────────────┘
       │                      ▲
       │             ┌────────┴────────┐
       │             │  Vector Store    │
       │             │  (FAISS Index)   │
       │             │  all-MiniLM-L6-v2│
       │             └─────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              Feature Modules                         │
│  clustering │ follow_up │ sensitive │ export         │
│  onboarding │ i18n      │ feedback                   │
└─────────────────────────────────────────────────────┘
```

**Data Pipeline:**
1. **Scraper** → Crawls GitLab Handbook & Direction pages
2. **Processor** → Chunks text + builds FAISS vector index with sentence embeddings
3. **Chatbot** → Retrieves relevant chunks + generates answers via Gemini LLM

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Google API Key** (free) — get one at [Google AI Studio](https://aistudio.google.com/apikey)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/genai-chatbot.git
cd genai-chatbot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and paste your GOOGLE_API_KEY
```

### 3. Scrape Data

```bash
python scraper.py
```

Crawls ~200-400 pages from GitLab's Handbook and Direction sites. Takes ~10–15 minutes.

### 4. Build Vector Index

```bash
python data_processor.py
```

Chunks the scraped content and builds a FAISS index. Takes ~1–2 minutes.

### 5. Launch the Chatbot

```bash
# If streamlit is on your PATH:
streamlit run app.py

# Or via Python module (always works):
python -m streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

---

## 📂 Project Structure

```
GenAI Chatbot/
├── app.py                 # Streamlit UI + all feature wiring
├── chatbot.py             # RAG chain (LangChain + Gemini)
├── scraper.py             # Web scraper for GitLab pages
├── data_processor.py      # Chunking + FAISS index builder
├── config.py              # Centralized configuration
├── clustering.py          # Topic cluster mapping
├── follow_up.py           # Follow-up question generator
├── sensitive.py           # Sensitive topic detector + disclaimer
├── export.py              # Bookmark export (Markdown / PDF)
├── onboarding.py          # Guided onboarding flow
├── i18n.py                # Translations for 5 languages
├── feedback.py            # Feedback store utilities
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
├── PROJECT_DOCS.md        # Full technical write-up
├── README.md              # This file
├── data/raw/              # Scraped data (gitignored)
└── vectorstore/           # FAISS index (gitignored)
```

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push your code to GitHub (commit `data/` and `vectorstore/` or build them on first launch)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo and set the main file to `app.py`
4. Add your `GOOGLE_API_KEY` in **Settings → Secrets**:
   ```toml
   GOOGLE_API_KEY = "your_key_here"
   ```
5. Deploy!

---

## 🔧 Configuration

All settings are in [`config.py`](config.py):

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_MODEL` | `gemini-2.5-flash` | Google Gemini model |
| `LLM_TEMPERATURE` | `0.3` | Response creativity (0=focused, 1=creative) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer for embeddings |
| `CHUNK_SIZE` | `1000` | Characters per text chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `RETRIEVER_K` | `4` | Number of chunks retrieved per query |
| `MAX_PAGES` | `120` | Maximum pages to scrape |

---

## 📝 License

This project is for educational purposes. GitLab's Handbook content is publicly available under their terms.
