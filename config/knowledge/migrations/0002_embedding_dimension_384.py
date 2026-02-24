# Migration: switch embedding dimension from 1536 (OpenAI) to 384 (Hugging Face)

from django.db import migrations
from pgvector.django import VectorField


def clear_embeddings(apps, schema_editor):
    """Clear existing embeddings so we can change column type (1536 -> 384)."""
    DocumentChunk = apps.get_model("knowledge", "DocumentChunk")
    DocumentChunk.objects.update(embedding=None)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(clear_embeddings, noop_reverse),
        migrations.RunSQL(
            "ALTER TABLE knowledge_documentchunk ALTER COLUMN embedding TYPE vector(384) USING NULL;",
            reverse_sql="ALTER TABLE knowledge_documentchunk ALTER COLUMN embedding TYPE vector(1536) USING NULL;",
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="documentchunk",
                    name="embedding",
                    field=VectorField(blank=True, dimensions=384, null=True),
                ),
            ],
        ),
    ]
