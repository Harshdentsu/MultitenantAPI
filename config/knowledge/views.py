from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import rag_ask


class AskView(APIView):
    """
    Private RAG endpoint: answer questions using only this organization's documents.
    Requires JWT authentication.
    """

    def post(self, request):
        question = request.data.get("question") if isinstance(request.data, dict) else None
        if not question or not str(question).strip():
            return Response(
                {"error": "Field 'question' is required and must be non-empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        answer = rag_ask(request.organization, str(question).strip())
        return Response({"answer": answer})

