import os
from pathlib import Path
from typing import List


def list_markdown_files(directory: Path) -> List[str]:
    """Return sorted Markdown filenames under *directory*."""
    if not directory.exists():
        return []
    return sorted(f.name for f in directory.glob('*.md') if f.is_file())


def read_markdown_file(directory: Path, name: str) -> str:
    """Return the text of *name* from *directory* or raise ``FileNotFoundError``."""
    # Prevent directory traversal
    if '/' in name or '\\' in name or not name.endswith('.md'):
        raise FileNotFoundError(name)
    path = directory / name
    if not path.is_file():
        raise FileNotFoundError(name)
    return path.read_text(encoding='utf-8')
