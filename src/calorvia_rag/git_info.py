from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[2]

def git_state():
    """Current commit, and whether the working tree has uncommitted changes."""
    def git(*args):
        return subprocess.run(['git', *args], cwd = REPO_ROOT, capture_output = True, text = True, check = True).stdout
    commit = git('rev-parse', 'HEAD').strip()
    dirty = git('status', '--porcelain') != ''
    return commit, dirty