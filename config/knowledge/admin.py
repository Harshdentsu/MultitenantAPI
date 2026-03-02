from django.contrib import admin
from .models import ConversationMessage, ConversationSession, DocumentChunk


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "organization", "order",)


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "created_at", "updated_at")
    search_fields = ("id",)


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "organization", "role", "created_at")
    list_filter = ("role", "organization")
    search_fields = ("session__id", "content")
