import requests
from flask import Blueprint, request, jsonify, render_template

bp = Blueprint('api_client', __name__)


def _parse_headers(text: str) -> dict:
    headers = {}
    for line in text.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            headers[key.strip()] = val.strip()
    return headers


@bp.route('/api_client', methods=['GET'])
def api_client_page():
    return render_template('api_client.html')


@bp.route('/api_client/openapi', methods=['GET'])
def load_openapi():
    url = request.args.get('url', '')
    if not url:
        return jsonify([])
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        spec = resp.json()
    except Exception:
        return jsonify([])
    paths = spec.get('paths', {})
    endpoints = []
    for path, methods in paths.items():
        if isinstance(methods, dict):
            for method in methods.keys():
                endpoints.append({'method': method.upper(), 'path': path})
    return jsonify(endpoints)


@bp.route('/api_client/send', methods=['POST'])
def send_request():
    method = request.form.get('method', 'GET').upper()
    url = request.form.get('url', '')
    headers_text = request.form.get('headers', '')
    body = request.form.get('body', '')
    headers = _parse_headers(headers_text)
    try:
        resp = requests.request(method, url, headers=headers, data=body, timeout=15)
    except Exception as e:
        return jsonify({'error': str(e)})
    result = {
        'status': resp.status_code,
        'headers': dict(resp.headers),
        'body': resp.text,
    }
    return jsonify(result)
