
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from django.conf import settings
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pgvector.django import CosineDistance

from documents.models import Document
from .models import ConversationMessage, ConversationSession, DocumentChunk

_embedding_model = None
_text_splitter = None
_chat_model = None


def _get_embedding_model() -> Any:
    global _embedding_model
    if _embedding_model is None:
        model_name = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        _embedding_model = OpenAIEmbeddings(
                model=model_name,
                dimensions=384,
                api_key=settings.OPENAI_API_KEY,
            )
    return _embedding_model


def _get_text_splitter() -> RecursiveCharacterTextSplitter:
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

   
    try:
        embedder = _get_embedding_model()
        embeddings = embedder.embed_documents(texts)
    except Exception as exc:
        return 0, f"Failed to generate embeddings: {exc}"
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
    top_k = top_k or getattr(settings, "RAG_TOP_K", 5)
    return (
        DocumentChunk.objects.filter(organization=organization)
        .exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )


def _get_or_create_session(organization, session_id: str | None) -> ConversationSession:
    if session_id:
        try:
            session_uuid = UUID(str(session_id))
            return ConversationSession.objects.get(id=session_uuid, organization=organization)
        except (ValueError, ConversationSession.DoesNotExist):
            pass
    return ConversationSession.objects.create(organization=organization)


def _build_history_messages(session: ConversationSession) -> list:
    history = (
        ConversationMessage.objects.filter(session=session, organization=session.organization)
        .order_by("-created_at")[:20]
    )
    history = list(reversed(history))
    messages = []
    for msg in history:
        if msg.role == ConversationMessage.ROLE_USER:
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == ConversationMessage.ROLE_ASSISTANT:
            messages.append(AIMessage(content=msg.content))
    return messages


def rag_ask(organization, question: str, session_id: str | None = None) -> tuple[str, str]:
    if not question or not question.strip():
        return "Please provide a question.", ""

    session = _get_or_create_session(organization, session_id)
    clean_question = question.strip()

    try:
        embedder = _get_embedding_model()
        query_embedding = embedder.embed_query(clean_question)
    except Exception:
        return (
            "Embedding model is unavailable. Check OPENAI_API_KEY, "
        ), str(session.id)
    chunks = search_chunks(organization, query_embedding)
    if not chunks:
        return (
            "I don't have any documents for your organization yet "
        ), str(session.id)
    context = "\n\n---\n\n".join(c.text for c in chunks)
    system = (
        "You are a helpful assistant. Answer the user's question using ONLY the following context "
        "from their organization's documents and prior conversation turns. "
        "If the context does not contain enough information, say so. "
        "Do not make up information or use external knowledge."
    )
    user = f"Context:\n{context}\n\nQuestion: {clean_question}"

    chat_model = _get_chat_model()
    messages = [SystemMessage(content=system), *_build_history_messages(session), HumanMessage(content=user)]
    response = chat_model.invoke(messages)
    answer = response.content or ""

    ConversationMessage.objects.bulk_create(
        [
            ConversationMessage(
                organization=organization,
                session=session,
                role=ConversationMessage.ROLE_USER,
                content=clean_question,
            ),
            ConversationMessage(
                organization=organization,
                session=session,
                role=ConversationMessage.ROLE_ASSISTANT,
                content=answer,
            ),
        ]
    )
    return answer, str(session.id)
