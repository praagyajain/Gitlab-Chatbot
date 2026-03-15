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
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

from config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    EMBEDDING_MODEL,
    VECTORSTORE_DIR,
    RETRIEVER_K,
)

# ── Prompt Template ───────────────────────────────────────────────────────────

SYSTEM_TEMPLATE = """You are **GitLab Guide**, a knowledgeable and friendly AI assistant 
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
{context}

QUESTION: {question}

HELPFUL ANSWER:"""

QA_PROMPT = PromptTemplate(
    template=SYSTEM_TEMPLATE,
    input_variables=["context", "question"],
)


# ── Chatbot Class ─────────────────────────────────────────────────────────────

class GitLabChatbot:
    """RAG chatbot backed by FAISS + Gemini."""

    def __init__(self):
        self.chain = None
        self.memory = None
        self._initialized = False

    def initialize(self) -> bool:
        """Load the vector store, LLM, and create the retrieval chain."""
        if self._initialized:
            return True

        # Validate prerequisites
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

        # Load embeddings & vector store
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        vectorstore = FAISS.load_local(
            VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": RETRIEVER_K},
        )

        # LLM
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=api_key,
            temperature=LLM_TEMPERATURE,
            convert_system_message_to_human=True,
        )

        # Memory (sliding window of 5 exchanges)
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )

        # Conversational retrieval chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True,
            verbose=False,
        )

        self._initialized = True
        return True

    def ask(self, question: str, role_context: str = "") -> dict:
        """
        Ask a question and get an answer with sources.

        Args:
            question: The user's question.
            role_context: Optional role context string. When non-empty, it is
                prepended to the question before passing to the chain.

        Returns:
            dict with keys:
                "answer"     – answer text (may contain HTML markup)
                "raw_answer" – plain-text answer with HTML tags stripped
                "sources"    – list of {title, url}
        """
        if not self._initialized:
            self.initialize()

        # Prepend role context when provided (Requirement 7.3)
        effective_question = (
            f"{role_context}\n\n{question}" if role_context else question
        )

        result = self.chain.invoke({"question": effective_question})

        # De-duplicate sources
        seen = set()
        sources = []
        for doc in result.get("source_documents", []):
            url = doc.metadata.get("source", "")
            title = doc.metadata.get("title", "Unknown")
            if url and url not in seen:
                seen.add(url)
                sources.append({"title": title, "url": url})

        answer = result.get("answer", "Sorry, I couldn't generate a response.")
        # Strip HTML tags for raw_answer (Requirement 7.4)
        raw_answer = re.sub(r"<[^>]+>", "", answer)

        return {
            "answer": answer,
            "raw_answer": raw_answer,
            "sources": sources,
        }

    def clear_memory(self):
        """Reset conversation history."""
        if self.memory:
            self.memory.clear()
