"""
Builds the web UI (web/ -> app/static/web) when its source has changed since the last build.

Run by start.bat before the panel starts. The build is skipped when nothing has changed, so starting the panel stays
quick. A hash of the source is stored alongside the build to tell whether it's current - file timestamps aren't
reliable after git checkouts.
"""
import hashlib
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
BUILD_DIR = os.path.join(BASE_DIR, "app", "static", "web")
BUILD_HASH_PATH = os.path.join(BUILD_DIR, ".source-hash")
INSTALL_HASH_PATH = os.path.join(WEB_DIR, "node_modules", ".lock-hash")

SOURCE_PATHS = ["src", "public", "index.html", "package.json", "package-lock.json", "vite.config.ts",
                "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json", "components.json"]


def hash_paths(paths):
    digest = hashlib.sha256()
    for relative in paths:
        path = os.path.join(WEB_DIR, relative)
        files = [path] if os.path.isfile(path) else sorted(
            os.path.join(root, name) for root, _, names in os.walk(path) for name in names)
        for file in files:
            digest.update(os.path.relpath(file, WEB_DIR).replace("\\", "/").encode())
            with open(file, "rb") as f:
                digest.update(f.read())
    return digest.hexdigest()


def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def run(*command):
    print(f"> {' '.join(command)}")
    # shell=True so Windows finds npm.cmd
    return subprocess.run(" ".join(command), cwd=WEB_DIR, shell=True).returncode == 0


def main():
    source_hash = hash_paths(SOURCE_PATHS)
    if read(BUILD_HASH_PATH) == source_hash:
        return 0

    built = os.path.exists(os.path.join(BUILD_DIR, "index.html"))
    if shutil.which("npm") is None:
        if built:
            print("Node.js isn't installed, so the web UI can't be rebuilt - using the existing build.")
            return 0
        print("The web UI needs building, which needs Node.js. Install it from https://nodejs.org and try again.")
        return 1

    print("Building the web UI...")
    lock_hash = hash_paths(["package-lock.json"])
    if read(INSTALL_HASH_PATH) != lock_hash:
        if not run("npm", "ci", "--no-audit", "--no-fund"):
            return 1
        with open(INSTALL_HASH_PATH, "w") as f:
            f.write(lock_hash)

    if not run("npm", "run", "build"):
        return 1

    with open(BUILD_HASH_PATH, "w") as f:
        f.write(source_hash)
    return 0


if __name__ == "__main__":
    sys.exit(main())
