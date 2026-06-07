from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
PUBLIC_DIR = ROOT / "public"
PUBLIC_STATIC_DIR = PUBLIC_DIR / "static"


def main() -> None:
    if PUBLIC_STATIC_DIR.exists():
        shutil.rmtree(PUBLIC_STATIC_DIR)
    PUBLIC_STATIC_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STATIC_DIR, PUBLIC_STATIC_DIR)


if __name__ == "__main__":
    main()
