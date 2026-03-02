from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import rag_ask


class AskView(APIView):

    def post(self, request):
        question = request.data.get("question") if isinstance(request.data, dict) else None
        session_id = request.data.get("session_id") if isinstance(request.data, dict) else None
        if not question or not str(question).strip():
            return Response(
                {"error": "Field 'question' is required and must be non-empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        answer, resolved_session_id = rag_ask(
            request.organization,
            str(question).strip(),
            str(session_id).strip() if session_id else None,
        )
        return Response({"answer": answer, "session_id": resolved_session_id})

