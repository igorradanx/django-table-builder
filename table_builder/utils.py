from rest_framework.views import exception_handler
from django.http import JsonResponse

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    return JsonResponse(response, safe=False)