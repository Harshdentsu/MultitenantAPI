from django.db import models
import uuid
from pgvector.django import VectorField

from core.models import TenantAwareModel

EMBEDDING_DIMENSION = 384


class DocumentChunk(TenantAwareModel):

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    text = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSION, null=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Chunk order within document")

    class Meta:
        ordering = ["document", "order"]
        indexes = [
            models.Index(fields=["organization", "document"]),
        ]

    def __str__(self):
        return f"Chunk {self.order} of {self.document_id}"


class ConversationSession(TenantAwareModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["organization", "updated_at"]),
        ]

    def __str__(self):
        return f"{self.organization_id}:{self.id}"


class ConversationMessage(TenantAwareModel):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    )

    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["organization", "session", "created_at"]),
        ]

    def __str__(self):
        return f"{self.session_id}:{self.role}"
