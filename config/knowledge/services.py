
import os
from pathlib import Path

from django.conf import settings
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pgvector.django import CosineDistance

from documents.models import Document
from .models import DocumentChunk

_embedding_model = None
_text_splitter = None
_chat_model = None


def _get_embedding_model() -> HuggingFaceEmbeddings:
    """Load LangChain HuggingFace embedding model once."""
    global _embedding_model
    if _embedding_model is None:
        model_name = getattr(
            settings,
            "HUGGINGFACE_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        _embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    return _embedding_model


def _get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Load LangChain text splitter once, using project settings for sizing."""
    global _text_splitter
    if _text_splitter is None:
        chunk_size = getattr(settings, "RAG_CHUNK_SIZE", 800)
        overlap = getattr(settings, "RAG_CHUNK_OVERLAP", 200)
        _text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
    return _text_splitter


def _get_chat_model() -> ChatOpenAI:
    """Lazy‑load LangChain ChatOpenAI model."""
    global _chat_model
    if _chat_model is None:
        chat_model_name = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4o-mini")
        _chat_model = ChatOpenAI(
            model=chat_model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )
    return _chat_model


def process_document(document: Document) -> tuple[int, str]:
    """
    Extract text from document file, chunk, embed, and save DocumentChunk rows for this org.
    Returns (chunks_created, error_message). error_message is empty on success.
    """
    if not document.file:
        return 0, "Document has no file"

    file_path = document.file.path
    if not os.path.exists(file_path):
        return 0, "File not found on disk"

    path = Path(file_path)
    if not path.exists():
        return 0, "File not found on disk"

    ext = path.suffix.lower()


    try:
        if ext == ".pdf":
            loader = PyMuPDFLoader(str(path))
        elif ext in (".docx", ".doc"):
            loader = Docx2txtLoader(str(path))
        elif ext == ".txt":
            loader = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True)
        else:
            loader = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True)
        base_docs = loader.load()
    except Exception:
        return 0, "Failed to read file"

    if not base_docs:
        return 0, "No text could be extracted from the file"

    splitter = _get_text_splitter()
    docs = splitter.split_documents(base_docs)
    texts = [d.page_content.strip() for d in docs if d.page_content.strip()]
    if not texts:
        return 0, "No chunks produced"

   
    embedder = _get_embedding_model()
    embeddings = embedder.embed_documents(texts)
    if len(embeddings) != len(texts):
        return 0, "Embedding count mismatch"
 
    DocumentChunk.objects.filter(document=document).delete()
    org = document.organization
    for i, (chunk_text, embedding) in enumerate(zip(texts, embeddings)):
        DocumentChunk.objects.create(
            organization=org,
            document=document,
            text=chunk_text,
            embedding=embedding,
            order=i,
        )
    return len(texts), ""


def search_chunks(organization, query_embedding: list, top_k: int = None):
    """Return top_k DocumentChunks for this org by cosine similarity (smaller distance = more similar)."""
    top_k = top_k or getattr(settings, "RAG_TOP_K", 5)
    return (
        DocumentChunk.objects.filter(organization=organization)
        .exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )


def rag_ask(organization, question: str) -> str:
    """
    Answer question using only this organization's documents (private RAG).
    Embeds question with Hugging Face, retrieves nearest chunks, then generates answer with OpenAI chat.
    """
    if not question or not question.strip():
        return "Please provide a question."

    embedder = _get_embedding_model()
    query_embedding = embedder.embed_query(question.strip())
    chunks = search_chunks(organization, query_embedding)
    if not chunks:
        return (
            "I don't have any documents for your organization yet, or they haven't been processed. "
            "Upload documents first, then try again."
        )
    context = "\n\n---\n\n".join(c.text for c in chunks)
    system = (
        "You are a helpful assistant. Answer the user's question using ONLY the following context "
        "from their organization's documents. If the context does not contain enough information, "
        "say so. Do not make up information or use external knowledge."
    )
    user = f"Context:\n{context}\n\nQuestion: {question}"

    chat_model = _get_chat_model()
    response = chat_model.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
    )
    return response.content or ""
