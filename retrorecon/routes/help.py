import os
import app
import markdown
from flask import Blueprint, request
from markupsafe import escape
from .dynamic import dynamic_template, render_from_payload, schema_registry, html_generator

bp = Blueprint('help', __name__)

@bp.route('/help/readme', methods=['GET'])
def help_readme():
    path = os.path.join(app.app.root_path, 'README.md')
    content = ''
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = markdown.markdown(f.read())
    return dynamic_template('help_readme.html', content=content)

@bp.route('/help/about', methods=['GET'])
def help_about():
    credits = [
        'the folks referenced in the README',
        'dagdotdev / original registry explorer project',
        'the shupandhack Discord',
    ]
    if request.args.get('legacy') == '1':
        return dynamic_template('help_about.html', version=app.APP_VERSION, credits=credits, use_legacy=True)
    credits_html = '<ul>' + ''.join(f'<li>{escape(c)}</li>' for c in credits) + '</ul>'
    payload = {
        'schema': 'help_about_page',
        'data': {
            'title': 'About RetroRecon',
            'version': app.APP_VERSION,
            'credits_html': credits_html,
        },
    }
    return render_from_payload(payload, schema_registry, html_generator)

@bp.route('/tools/readme', methods=['GET'])
def help_readme_full():
    return app.index()

@bp.route('/tools/about', methods=['GET'])
def help_about_full():
    return app.index()
