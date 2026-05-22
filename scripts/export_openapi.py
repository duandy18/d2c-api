import json
from pathlib import Path

from app.main import app


def main() -> None:
    output_path = Path("openapi.json")
    output_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"exported: {output_path}")


if __name__ == "__main__":
    main()
