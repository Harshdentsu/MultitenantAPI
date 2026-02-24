from django.urls import path
from .views import DocumentListView, DocumentUploadView

urlpatterns = [
    path("", DocumentListView.as_view()),
    path("upload/", DocumentUploadView.as_view()),
]