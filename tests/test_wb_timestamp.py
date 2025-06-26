import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrorecon.filters import wb_timestamp


def test_wb_timestamp_basic():
    assert wb_timestamp('20240102030405') == '2024-01-02 03:04:05'


def test_wb_timestamp_invalid():
    assert wb_timestamp('badval') == 'badval'
    assert wb_timestamp(None) == ''
