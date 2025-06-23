import io
import json
import datetime
import os
import base64
import urllib.parse
import requests
import zipfile
import app
from retrorecon import screenshot_service, jwt_service, sitezip_service, app_utils
from flask import (
    Blueprint,
    request,
    Response,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash,
    send_file,
    current_app,
)

bp = Blueprint('tools', __name__)

@bp.route('/text_tools', methods=['GET'])
def text_tools_page():
    return render_template('text_tools.html')


@bp.route('/tools/text_tools', methods=['GET'])
def text_tools_full_page():
    """Serve the full page with Text Tools overlay loaded."""
    return app.index()


def _get_text_param():
    text = request.form.get('text', '')
    if len(text.encode('utf-8')) > app.TEXT_TOOLS_LIMIT:
        return None
    return text


@bp.route('/tools/base64_decode', methods=['POST'])
def base64_decode_route():
    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    try:
        decoded = base64.b64decode(text, validate=True)
        decoded.decode('utf-8')
    except Exception:
        return ('Invalid Base64 data', 400)
    return Response(decoded, mimetype='text/plain')


@bp.route('/tools/base64_encode', methods=['POST'])
def base64_encode_route():
    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
    return Response(encoded, mimetype='text/plain')


@bp.route('/tools/url_decode', methods=['POST'])
def url_decode_route():
    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    try:
        decoded = urllib.parse.unquote_plus(text)
    except Exception:
        return ('Invalid URL encoding', 400)
    return Response(decoded, mimetype='text/plain')


@bp.route('/tools/url_encode', methods=['POST'])
def url_encode_route():
    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    encoded = urllib.parse.quote_plus(text)
    return Response(encoded, mimetype='text/plain')


@bp.route('/jwt_tools', methods=['GET'])
def jwt_tools_page():
    return render_template('jwt_tools.html')


@bp.route('/tools/jwt', methods=['GET'])
def jwt_tools_full_page():
    return app.index()


@bp.route('/tools/jwt_decode', methods=['POST'])
def jwt_decode_route():
    token = request.form.get('token', '')
    if len(token.encode('utf-8')) > app.TEXT_TOOLS_LIMIT:
        return ('Request too large', 400)
    if not app_utils._db_loaded():
        return jsonify({'error': 'no_db'}), 400
    try:
        header = jwt_service.jwt.get_unverified_header(token)
        payload = jwt_service.jwt.decode(token, options={'verify_signature': False})
    except Exception as e:
        return (f'Invalid JWT: {e}', 400)

    result: dict = {"header": header, "payload": payload}

    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    if isinstance(payload, dict):
        for field in ["iat", "nbf", "exp"]:
            val = payload.get(field)
            if isinstance(val, (int, float)):
                dt = datetime.datetime.fromtimestamp(val, datetime.timezone.utc)
                result[f"{field}_readable"] = dt.strftime("%Y-%m-%d %H:%M:%S")
    exp_val = payload.get("exp")
    if isinstance(exp_val, (int, float)):
        result["expired"] = now > exp_val
        result["exp_readable"] = datetime.datetime.fromtimestamp(exp_val, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        result["expired"] = False

    alg = header.get("alg", "").lower()
    weak_algs = {"none", "hs256", "hs384", "hs512"}
    result["alg_warning"] = alg in weak_algs

    key_warning = False
    known_keys = ["secret", "secret123", "changeme", "password"]
    for k in known_keys:
        try:
            jwt_service.jwt.decode(
                token,
                k,
                algorithms=[header.get("alg", "")],
                options={"verify_signature": True, "verify_exp": False},
            )
            key_warning = True
            break
        except jwt_service.jwt.InvalidSignatureError:
            continue
        except Exception:
            continue
    result["key_warning"] = key_warning

    notes = []
    if result.get("alg_warning"):
        notes.append("Weak algorithm")
    if result.get("key_warning"):
        notes.append("Weak key")
    if result.get("exp_readable"):
        note = f"exp {result['exp_readable']}"
        if result.get("expired"):
            note += " expired"
        notes.append(note)
    try:
        jwt_service.log_jwt_entry(token, header, payload, "; ".join(notes))
    except Exception:
        pass

    return jsonify(result)


@bp.route('/tools/jwt_encode', methods=['POST'])
def jwt_encode_route():
    raw = request.form.get('payload', '')
    if len(str(raw).encode('utf-8')) > app.TEXT_TOOLS_LIMIT:
        return ('Request too large', 400)
    secret = request.form.get('secret') or None

    def _parse(text: str):
        try:
            return json.loads(text)
        except Exception:
            try:
                import ast
                return ast.literal_eval(text)
            except Exception:
                return None

    payload = _parse(raw)
    if payload is None:
        for sep in ['}\n{', '}\r\n{']:
            if sep in raw:
                candidate = '{' + raw.split(sep, 1)[1]
                payload = _parse(candidate)
                if payload is not None:
                    break
    if payload is None:
        payload = {}
    if secret:
        token = jwt_service.jwt.encode(payload, secret, algorithm='HS256')
    else:
        token = jwt_service.jwt.encode(payload, '', algorithm='none')
    if isinstance(token, bytes):
        token = token.decode('ascii')
    return Response(token, mimetype='text/plain')


@bp.route('/jwt_cookies', methods=['GET'])
def jwt_cookies_route():
    if not app_utils._db_loaded():
        return jsonify([])
    rows = jwt_service.export_jwt_cookie_data()[:50]
    return jsonify(rows)


@bp.route('/delete_jwt_cookies', methods=['POST'])
def delete_jwt_cookies_route():
    if not app_utils._db_loaded():
        return ('', 400)
    ids = [int(i) for i in request.form.getlist('ids') if i.isdigit()]
    if not ids:
        return ('', 400)
    jwt_service.delete_jwt_cookies(ids)
    return ('', 204)


@bp.route('/update_jwt_cookie', methods=['POST'])
def update_jwt_cookie_route():
    if not app_utils._db_loaded():
        return ('', 400)
    jid = request.form.get('id', type=int)
    notes = request.form.get('notes', '').strip()
    if not jid:
        return ('', 400)
    jwt_service.update_jwt_cookie(jid, notes)
    return ('', 204)


@bp.route('/export_jwt_cookies', methods=['GET'])
def export_jwt_cookies_route():
    if not app_utils._db_loaded():
        return jsonify([])
    ids = [int(i) for i in request.args.getlist('id') if i.isdigit()]
    rows = jwt_service.export_jwt_cookie_data(ids if ids else None)
    return jsonify(rows)


@bp.route('/screenshotter', methods=['GET'])
def screenshotter_page():
    return render_template('screenshotter.html')


@bp.route('/tools/screenshotter', methods=['GET'])
def screenshotter_full_page():
    return app.index()


@bp.route('/tools/screenshot', methods=['POST'])
def screenshot_route():
    if not app_utils._db_loaded():
        return jsonify({'error': 'no_db'}), 400
    url = request.form.get('url', '').strip()
    if not url:
        return ('Missing URL', 400)
    agent = request.form.get('user_agent', '').strip()
    spoof = request.form.get('spoof_referrer', '0') == '1'
    try:
        img_bytes = screenshot_service.take_screenshot(url, agent, spoof)
    except Exception as e:
        return (f'Error taking screenshot: {e}', 500)
    ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    fname = f'shot_{ts}.png'
    thumb = f'shot_{ts}_th.png'
    os.makedirs(screenshot_service.get_screenshot_dir(), exist_ok=True)
    full_path = os.path.join(screenshot_service.get_screenshot_dir(), fname)
    with open(full_path, 'wb') as f:
        f.write(img_bytes)
    thumb_path = os.path.join(screenshot_service.get_screenshot_dir(), thumb)
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        img.thumbnail((160, 160))
        img.save(thumb_path, format='PNG')
    except Exception as e:
        app.logger.debug('thumbnail generation failed: %s', e)
        with open(thumb_path, 'wb') as f:
            f.write(img_bytes)
    sid = screenshot_service.save_screenshot_record(url, fname, thumb, 'GET')
    return jsonify({'id': sid})


@bp.route('/screenshots', methods=['GET'])
def screenshots_route():
    if not app_utils._db_loaded():
        return jsonify([])
    rows = screenshot_service.list_screenshot_data()
    for r in rows:
        r['file'] = url_for('static', filename='screenshots/' + r['screenshot_path'])
        r['preview'] = url_for('static', filename='screenshots/' + r['thumbnail_path'])
    return jsonify(rows)


@bp.route('/delete_screenshots', methods=['POST'])
def delete_screenshots_route():
    if not app_utils._db_loaded():
        return ('', 400)
    ids = [int(i) for i in request.form.getlist('ids') if i.isdigit()]
    if not ids:
        return ('', 400)
    screenshot_service.delete_screenshots(ids)
    return ('', 204)


@bp.route('/site2zip', methods=['GET'])
def site2zip_page():
    return render_template('site2zip.html')


@bp.route('/tools/site2zip', methods=['GET'])
def site2zip_full_page():
    return app.index()

@bp.route('/layerpeek', methods=['GET'])
def layerpeek_page():
    return render_template('layerslayer.html')

@bp.route('/tools/layerpeek', methods=['GET'])
def layerpeek_full_page():
    return app.index()


@bp.route('/tools/site2zip', methods=['POST'])
def site2zip_route():
    if not app_utils._db_loaded():
        return jsonify({'error': 'no_db'}), 400
    url = request.form.get('url', '').strip()
    if not url:
        return ('Missing URL', 400)
    agent = request.form.get('agent', '').strip()
    spoof = request.form.get('spoof_referrer', '0') == '1'
    try:
        zip_bytes, shot_bytes = sitezip_service.capture_site(url, agent, spoof)
    except Exception as e:
        return (f'Error capturing site: {e}', 500)
    ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    zip_name = f'site_{ts}.zip'
    shot_name = f'site_{ts}.png'
    thumb_name = f'site_{ts}_th.png'
    os.makedirs(sitezip_service.get_sitezip_dir(), exist_ok=True)
    with open(os.path.join(sitezip_service.get_sitezip_dir(), zip_name), 'wb') as f:
        f.write(zip_bytes)
    shot_path = os.path.join(sitezip_service.get_sitezip_dir(), shot_name)
    with open(shot_path, 'wb') as f:
        f.write(shot_bytes)
    thumb_path = os.path.join(sitezip_service.get_sitezip_dir(), thumb_name)
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(shot_bytes))
        img.thumbnail((160, 160))
        img.save(thumb_path, format='PNG')
    except Exception as e:
        current_app.logger.debug('thumbnail generation failed: %s', e)
        with open(thumb_path, 'wb') as f:
            f.write(shot_bytes)
    sid = sitezip_service.save_sitezip_record(url, zip_name, shot_name, thumb_name, 'GET')
    return jsonify({'id': sid})


@bp.route('/sitezips', methods=['GET'])
def sitezips_route():
    if not app_utils._db_loaded():
        return jsonify([])
    rows = sitezip_service.list_sitezip_data()
    for r in rows:
        r['zip'] = url_for('static', filename='sitezips/' + r['zip_path'])
        r['preview'] = url_for('static', filename='sitezips/' + r['thumbnail_path'])
    return jsonify(rows)


@bp.route('/download_sitezip/<int:sid>', methods=['GET'])
def download_sitezip_route(sid: int):
    if not app_utils._db_loaded():
        return ('', 400)
    rows = sitezip_service.list_sitezip_data([sid])
    if not rows:
        return ('Not found', 404)
    zip_path = os.path.join(sitezip_service.get_sitezip_dir(), rows[0]['zip_path'])
    return send_file(zip_path, mimetype='application/zip', as_attachment=True, download_name=rows[0]['zip_path'])


@bp.route('/delete_sitezips', methods=['POST'])
def delete_sitezips_route():
    if not app_utils._db_loaded():
        return ('', 400)
    ids = [int(i) for i in request.form.getlist('ids') if i.isdigit()]
    if not ids:
        return ('', 400)
    sitezip_service.delete_sitezips(ids)
    return ('', 204)


@bp.route('/tools/webpack-zip', methods=['POST'])
def webpack_zip():
    map_url = request.form.get('map_url', '').strip()
    if not map_url:
        flash("No .js.map URL provided.", "error")
        return redirect(url_for('index'))
    try:
        resp = requests.get(map_url, timeout=15)
        resp.raise_for_status()
        raw_text = resp.text
        map_data = json.loads(raw_text)
        sources = map_data.get('sources', [])
        sources_content = map_data.get('sourcesContent', [])
        if len(sources_content) != len(sources):
            flash(
                "Warning: sourcesContent length does not match sources length. Some files may be skipped.",
                "warning"
            )
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, src_path in enumerate(sources):
                filename_in_zip = src_path.replace('\\', '/').lstrip('/')
                if idx < len(sources_content) and sources_content[idx] is not None:
                    file_bytes = sources_content[idx].encode('utf-8')
                else:
                    continue
                zipf.writestr(filename_in_zip, file_bytes)
        zip_buffer.seek(0)
        original_map_name = map_url.rstrip('/').split('/')[-1]
        zip_filename = original_map_name.replace('.map', '.zip')
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching .js.map: {e}", "error")
        return redirect(url_for('index'))
    except (json.JSONDecodeError, KeyError) as e:
        flash(f"Error parsing .js.map JSON: {e}", "error")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Unexpected server error: {e}", "error")
        return redirect(url_for('index'))
