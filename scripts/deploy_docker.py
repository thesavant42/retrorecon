import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_NAME = os.environ.get("IMAGE_NAME", "savant42/retrorecon")
IMAGE_TAG = os.environ.get("IMAGE_TAG", "edge")
DOCKERHUB_USERNAME = os.environ.get("DOCKERHUB_USERNAME")
DOCKERHUB_PAT = os.environ.get("DOCKERHUB_PAT")


def run(cmd, **kwargs):
    """Run a command, raising an exception if it fails."""
    print("$", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)


def docker_login():
    if not DOCKERHUB_USERNAME or not DOCKERHUB_PAT:
        raise SystemExit("DOCKERHUB_USERNAME and DOCKERHUB_PAT must be set")
    print("Logging in to Docker Hub...")
    run([
        "docker",
        "login",
        "--username",
        DOCKERHUB_USERNAME,
        "--password-stdin",
    ], input=DOCKERHUB_PAT.encode())


def build_image():
    print(f"Building {IMAGE_NAME}:{IMAGE_TAG}...")
    run(["docker", "build", "-t", f"{IMAGE_NAME}:{IMAGE_TAG}", str(REPO_ROOT)])


def push_image():
    print(f"Pushing {IMAGE_NAME}:{IMAGE_TAG}...")
    run(["docker", "push", f"{IMAGE_NAME}:{IMAGE_TAG}"])


def main() -> None:
    docker_login()
    build_image()
    push_image()


if __name__ == "__main__":
    main()
