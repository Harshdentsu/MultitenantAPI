from django.db import models
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
