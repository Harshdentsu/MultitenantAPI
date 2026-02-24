# Generated migration for knowledge app with pgvector

import django.db.models.deletion
from django.db import migrations, models
from pgvector.django import VectorExtension, VectorField


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("documents", "0001_initial"),
    ]

    operations = [
        VectorExtension(),
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("embedding", VectorField(blank=True, dimensions=1536, null=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="documents.document")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.organization")),
            ],
            options={
                "ordering": ["document", "order"],
            },
        ),
        migrations.AddIndex(
            model_name="documentchunk",
            index=models.Index(fields=["organization", "document"], name="knowledge_do_organiz_4a0b0d_idx"),
        ),
    ]
