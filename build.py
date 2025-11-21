import os
import tarfile
from pathlib import Path


APP_NAME = os.environ["npm_package_name"]
OUT_DIR = Path("public")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    with tarfile.open(OUT_DIR / f"{APP_NAME}.tgz", "w:gz") as archive:
        archive.add("src", APP_NAME)


if __name__ == '__main__':
    main()
