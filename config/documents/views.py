from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer
from knowledge.services import process_document


class DocumentListView(APIView):
    def get(self, request):
        documents = Document.objects.filter(organization=request.organization).order_by("-uploaded_at")
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)


class DocumentUploadView(APIView):

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file provided"}, status=400)

        document = Document.objects.create(
            file=file,
            organization=request.organization,
        )
        chunks_created, processing_error = process_document(document)
        serializer = DocumentSerializer(document)
        data = dict(serializer.data)
        data["chunks_created"] = chunks_created
        if processing_error:
            data["processing_warning"] = processing_error
        return Response(data, status=201)