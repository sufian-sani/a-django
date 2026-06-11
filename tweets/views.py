from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def tweet_list(request):
    tweets = [
        {"id": 1, "text": "Hello from sample API", "author": "demo"},
        {"id": 2, "text": "Django REST Framework is working", "author": "admin"},
    ]
    return Response(tweets)


@api_view(["POST"])
@permission_classes([AllowAny])
def tweet_create(request):
    text = request.data.get("text")

    if not text:
        return Response(
            {"detail": "Text is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tweet = {
        "id": 3,
        "text": text,
        "author": request.data.get("author", "demo"),
    }
    return Response(tweet, status=status.HTTP_201_CREATED)
