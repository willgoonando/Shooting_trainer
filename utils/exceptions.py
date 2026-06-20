from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'code': response.status_code,
            'message': str(exc.detail) if hasattr(exc, 'detail') else '请求错误',
            'data': response.data,
        }
    return response
