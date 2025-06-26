import app
from retrorecon.filters import human_ts


def test_human_ts_valid():
    assert human_ts('20240102123456') == '2024-01-02 12:34:56'


def test_human_ts_invalid():
    assert human_ts('') == ''
    assert human_ts('abcdef') == 'abcdef'
