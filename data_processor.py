"""
Data processing pipeline: load scraped pages, chunk text, generate
embeddings, and build a FAISS vector index.

Usage:
    python data_processor.py
"""

import json
import os
import glob

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import (
    RAW_DATA_DIR,
    VECTORSTORE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
)


def load_scraped_data() -> list[Document]:
    """Load all scraped JSON files and convert to LangChain Documents."""
    documents = []
    json_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))

    if not json_files:
        print("⚠ No scraped data found. Run `python scraper.py` first.")
        return documents

    print(f"📂 Found {len(json_files)} scraped pages")

    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        doc = Document(
            page_content=data["content"],
            metadata={
                "source": data["url"],
                "title": data["title"],
                "source_type": data.get("source_type", "unknown"),
            },
        )
        documents.append(doc)

    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split documents into smaller chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"✂️  Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def build_vectorstore(chunks: list[Document]) -> FAISS:
    """Generate embeddings and build a FAISS index."""
    print(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("🔨 Building FAISS index... (this may take a minute)")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)
    vectorstore.save_local(VECTORSTORE_DIR)
    print(f"💾 FAISS index saved to: {VECTORSTORE_DIR}")

    return vectorstore


def main():
    print("=" * 60)
    print("  Data Processor — Chunk & Index")
    print("=" * 60)

    # Step 1: Load scraped data
    documents = load_scraped_data()
    if not documents:
        return

    # Step 2: Chunk
    chunks = chunk_documents(documents)

    # Step 3: Build & persist FAISS index
    build_vectorstore(chunks)

    print(f"\n{'=' * 60}")
    print(f"  ✅ Vector store ready! {len(chunks)} chunks indexed.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
