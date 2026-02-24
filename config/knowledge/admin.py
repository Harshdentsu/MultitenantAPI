from django.contrib import admin
from .models import DocumentChunk


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "organization", "order",)