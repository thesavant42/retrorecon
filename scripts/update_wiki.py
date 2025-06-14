import os
import shutil
import subprocess
import tempfile
from pathlib import Path

WIKI_URL = os.environ.get('WIKI_URL', 'https://github.com/thesavant42/retrorecon.wiki.git')
GIT_USER_NAME = os.environ.get('GIT_USER_NAME', 'retrorecon-bot')
GIT_USER_EMAIL = os.environ.get('GIT_USER_EMAIL', 'actions@github.com')
REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd=None):
    """Run a shell command and raise if it fails."""
    subprocess.check_call(cmd, cwd=cwd)


def setup_git_config(cwd: Path) -> None:
    """Configure git user.name and user.email."""
    run(['git', 'config', 'user.name', GIT_USER_NAME], cwd=cwd)
    run(['git', 'config', 'user.email', GIT_USER_EMAIL], cwd=cwd)

def copy_markdown(src_root: Path, dest_root: Path) -> None:
    """Copy all Markdown files from src_root into dest_root preserving paths."""
    for md in src_root.rglob('*.md'):
        if '.git' in md.parts or 'node_modules' in md.parts:
            continue
        rel = md.relative_to(src_root)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(md, dest)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        run(['git', 'clone', WIKI_URL, tmpdir])
        wiki_path = Path(tmpdir)

        setup_git_config(wiki_path)

        # remove existing files except .git
        for item in wiki_path.iterdir():
            if item.name == '.git':
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        copy_markdown(REPO_ROOT, wiki_path)

        run(['git', 'add', '.'], cwd=wiki_path)
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=wiki_path,
                                capture_output=True, text=True, check=True)
        if status.stdout.strip():
            run(['git', 'commit', '-m', 'Update wiki pages from repository markdown'], cwd=wiki_path)
            run(['git', 'push'], cwd=wiki_path)


if __name__ == '__main__':
    main()
