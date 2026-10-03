import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the youtdown web service.")
    parser.add_argument("--reload", action="store_true", help="Reload on code changes.")
    args = parser.parse_args()
    uvicorn.run("youtdown.web:app", host="127.0.0.1", port=8001, reload=args.reload)


if __name__ == "__main__":
    main()
