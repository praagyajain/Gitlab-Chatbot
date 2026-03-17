"""
RAG chatbot backend using LangChain, FAISS, and Google Gemini.

Provides a GitLabChatbot class that loads the vector index and answers
user questions with source citations.
"""

import os
import re
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    EMBEDDING_MODEL,
    VECTORSTORE_DIR,
    RETRIEVER_K,
)

# ── Prompt Templates ──────────────────────────────────────────────────────────

CONDENSE_SYSTEM = (
    "Given a chat history and the latest user question which might reference "
    "context in the chat history, formulate a standalone question which can be "
    "understood without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CONDENSE_SYSTEM),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

QA_SYSTEM = """You are **GitLab Guide**, a knowledgeable and friendly AI assistant 
specializing in GitLab's Handbook and Product Direction.

RULES:
1. Answer the question using ONLY the context provided below.
2. If the context does not contain enough information, say:
   "I don't have enough information from the GitLab Handbook or Direction pages to answer that. 
   You might want to check handbook.gitlab.com directly."
3. Be concise but thorough. Use bullet points or numbered lists when helpful.
4. When referencing specific topics, mention which section of the handbook or direction page 
   the information comes from.
5. Be professional yet approachable — like a helpful colleague.

CONTEXT:
{context}"""

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", QA_SYSTEM),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


# ── Chatbot Class ─────────────────────────────────────────────────────────────

class GitLabChatbot:
    """RAG chatbot backed by FAISS + Gemini."""

    def __init__(self):
        self.chain = None
        self._llm = None  # stored for follow-up generation
        self._retriever = None
        self.chat_history = []
        self._initialized = False

    def initialize(self) -> bool:
        """Load the vector store, LLM, and create the retrieval chain."""
        if self._initialized:
            return True

        api_key = GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. "
                "Please add it to your .env file or Streamlit secrets."
            )

        if not os.path.exists(VECTORSTORE_DIR):
            raise FileNotFoundError(
                f"Vector store not found at {VECTORSTORE_DIR}. "
                "Run `python scraper.py` then `python data_processor.py` first."
            )

        # Embeddings & vector store
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        vectorstore = FAISS.load_local(
            VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True
        )
        self._retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": RETRIEVER_K},
        )

        # LLM
        self._llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=api_key,
            temperature=LLM_TEMPERATURE,
        )

        # History-aware retriever: condenses follow-up questions using chat history
        condense_chain = CONDENSE_PROMPT | self._llm | StrOutputParser()

        def history_aware_retrieve(inputs: dict) -> list:
            chat_history = inputs.get("chat_history", [])
            question = inputs["input"]
            # Only condense if there's prior history
            if chat_history:
                standalone = condense_chain.invoke({
                    "input": question,
                    "chat_history": chat_history,
                })
            else:
                standalone = question
            return self._retriever.invoke(standalone)

        # QA chain: formats docs into context string, then prompts LLM
        def qa_invoke(inputs: dict) -> str:
            docs = inputs["context"]
            context_str = "\n\n".join(doc.page_content for doc in docs)
            return (
                QA_PROMPT
                | self._llm
                | StrOutputParser()
            ).invoke({
                "input": inputs["input"],
                "chat_history": inputs.get("chat_history", []),
                "context": context_str,
            })

        # Full chain
        def full_chain(inputs: dict) -> dict:
            docs = history_aware_retrieve(inputs)
            answer = qa_invoke({**inputs, "context": docs})
            return {"answer": answer, "context": docs}

        self.chain = RunnableLambda(full_chain)
        self._initialized = True
        return True

    def ask(self, question: str, role_context: str = "") -> dict:
        """Ask a question and get an answer with sources."""
        if not self._initialized:
            self.initialize()

        effective_question = (
            f"{role_context}\n\n{question}" if role_context else question
        )

        result = self.chain.invoke({
            "input": effective_question,
            "chat_history": self.chat_history,
        })

        answer = result.get("answer", "Sorry, I couldn't generate a response.")

        # Sliding window history (last 5 exchanges)
        self.chat_history.append(HumanMessage(content=effective_question))
        self.chat_history.append(AIMessage(content=answer))
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

        # De-duplicate sources
        seen = set()
        sources = []
        for doc in result.get("context", []):
            url = doc.metadata.get("source", "")
            title = doc.metadata.get("title", "Unknown")
            if url and url not in seen:
                seen.add(url)
                sources.append({"title": title, "url": url})

        raw_answer = re.sub(r"<[^>]+>", "", answer)

        return {
            "answer": answer,
            "raw_answer": raw_answer,
            "sources": sources,
        }

    def clear_memory(self):
        """Reset conversation history."""
        self.chat_history = []
