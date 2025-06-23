from flask import Response


def add_no_cache_headers(response: Response) -> Response:
    """Disable caching so templates always reload."""
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response
