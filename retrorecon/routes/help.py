import os
import app
import markdown
from flask import Blueprint, render_template

bp = Blueprint('help', __name__)

@bp.route('/help/readme', methods=['GET'])
def help_readme():
    path = os.path.join(app.app.root_path, 'README.md')
    content = ''
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = markdown.markdown(f.read())
    return render_template('help_readme.html', content=content)

@bp.route('/help/about', methods=['GET'])
def help_about():
    credits = [
        'the folks referenced in the README',
        'dagdotdev / original registry explorer project',
        'the shupandhack Discord',
    ]
    return render_template('help_about.html', version=app.APP_VERSION, credits=credits)

@bp.route('/tools/readme', methods=['GET'])
def help_readme_full():
    return app.index()

@bp.route('/tools/about', methods=['GET'])
def help_about_full():
    return app.index()
