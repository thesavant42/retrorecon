import os, sys; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import yaml
from app import app

def convert(path: str) -> str:
    out = ''
    i = 0
    while i < len(path):
        if path[i] == '<':
            j = path.index('>', i)
            inner = path[i+1:j]
            name = inner.split(':')[-1]
            if '=' in name:
                name = name.split('=')[0]
            out += '{' + name + '}'
            i = j + 1
        else:
            out += path[i]
            i += 1
    return out

paths = {}
for rule in app.url_map.iter_rules():
    if rule.endpoint == 'static':
        continue
    op = {}
    for method in sorted(rule.methods - {'HEAD', 'OPTIONS'}):
        op[method.lower()] = {
            'summary': f'{method} {rule.rule}',
            'responses': {
                '200': {'description': 'Successful response'}
            }
        }
    paths[convert(rule.rule)] = op

# stub routes for manual packets
paths['/manual_packet'] = {
    'post': {
        'summary': 'Craft a manual packet (stub)',
        'responses': {'200': {'description': 'OK'}}
    }
}
paths['/manual_packet/{id}'] = {
    'get': {
        'summary': 'Retrieve manual packet (stub)',
        'responses': {'200': {'description': 'OK'}}
    }
}

openapi = {
    'openapi': '3.0.0',
    'info': {
        'title': 'Retrorecon API',
        'version': '1.1'
    },
    'paths': paths
}

with open('static/openapi.yaml', 'w') as fh:
    yaml.dump(openapi, fh, sort_keys=False)
