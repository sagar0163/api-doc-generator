from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET", "POST"])
def user_list(request):
    """List users or create a new one."""
    return Response(["a", "b"])


def health(request):
    return Response({"status": "ok"})