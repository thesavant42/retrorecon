import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_subdomonster_js_has_checkbox_column():
    js = Path('static/subdomonster.js').read_text()
    assert '<col class="w-1-6em checkbox-col"' in js
    assert '<th class="w-1-6em checkbox-col text-center"' in js
    assert 'subdomonster-col-widths' in js
    assert 'checkbox-col text-center' in js
    assert 'subdomonster-search' not in js
    assert 'subdomonster-api-key' not in js
