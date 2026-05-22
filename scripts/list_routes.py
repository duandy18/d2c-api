from app.main import app


def main() -> None:
    for route in app.routes:
        methods = ",".join(sorted(route.methods or []))
        print(f"{methods:20s} {route.path}")


if __name__ == "__main__":
    main()
