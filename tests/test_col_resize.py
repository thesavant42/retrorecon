import json
import subprocess
from pathlib import Path

def run_js(code):
    result = subprocess.run(['node', '-e', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()

def test_get_col_widths_matches_count(tmp_path):
    js = Path('static/col_resize.js').read_text()
    script = f"""
global.window = {{}};
{js}
global.localStorage = {{store:{{}}, getItem(k){{return this.store[k];}}, setItem(k,v){{this.store[k]=v;}}}};
localStorage.setItem('w', JSON.stringify({{'0':'40px','1':'70px'}}));
const out = getColWidths('w',2);
console.log(JSON.stringify(out));
"""
    out = run_js(script)
    assert json.loads(out) == {'0':'40px','1':'70px'}

def test_get_col_widths_mismatch_count(tmp_path):
    js = Path('static/col_resize.js').read_text()
    script = f"""
global.window = {{}};
{js}
global.localStorage = {{store:{{}}, getItem(k){{return this.store[k];}}, setItem(k,v){{this.store[k]=v;}}}};
localStorage.setItem('w', JSON.stringify({{'0':'40px'}}));
const out = getColWidths('w',2);
console.log(JSON.stringify(out));
"""
    out = run_js(script)
    assert json.loads(out) == {}

