from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse


START = "<!-- STREAMLIT-LIVE-START -->"
END = "<!-- STREAMLIT-LIVE-END -->"


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the live Streamlit URL in the main README.")
    parser.add_argument("--url", required=True, help="Public https:// Streamlit application URL")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SystemExit("URL must be a valid public https:// address")

    readme = Path(__file__).resolve().parents[1] / "README.md"
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README live-demo markers were not found")
    before, remainder = text.split(START, 1)
    _, after = remainder.split(END, 1)
    replacement = f'{START}\n[Open the Live Streamlit Application]({args.url})\n{END}'
    readme.write_text(before + replacement + after, encoding="utf-8")
    print(f"README updated with {args.url}")


if __name__ == "__main__":
    main()