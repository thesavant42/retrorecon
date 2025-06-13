import importlib
from scripts import check_theme_elements


def test_theme_selectors_have_styles():
    rows = check_theme_elements.check_styles()
    missing = [r for r in rows if not r['actual']]
    assert not missing, f"Missing styles for: {[r['name'] for r in missing]}"
