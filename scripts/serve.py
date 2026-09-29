"""Serve the web dashboard without implicitly preparing data or training."""
import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    import uvicorn
    uvicorn.run("backend.main:app", host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
