from rest_framework import status
from rest_framework.response import Response

from common import signal_handler

def resolve_response(data):
    if not data:
        return Response(data, status=status.HTTP_200_OK)
    if data.pop("error", False):
        error_msg = data.pop("msg", None)
        if not error_msg:
            error_msg = data.pop("message", "Unknown Error")
        data["error"] = error_msg
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(data, status=status.HTTP_200_OK)
