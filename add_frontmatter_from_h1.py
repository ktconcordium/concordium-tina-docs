#!/usr/bin/env python3
"""
Add YAML frontmatter from the first H1 heading AND rename .md → .mdx.

Converts:

    # Set up the Concordium Wallet for Web

into:

    ---
    title: "Set up the Concordium Wallet for Web"
    ---

and removes the original H1.

Also renames all `.md` files to `.mdx`.

Usage:
    python update_docs.py content/docs
"""

import re
import sys
from pathlib import Path


# ---------------- HELPERS ---------------- #

def extract_h1(text: str):
    """
    Find first markdown H1 (`# Heading`) and return (title, body_without_h1).
    """
    pattern = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return None, text

    title = m.group(1).strip()

    start, end = m.span()
    new_text = text[:start] + text[end:]  # remove the H1 line

    # remove leading blank line
    new_text = re.sub(r"^\s*\n", "", new_text, count=1)

    return title, new_text.lstrip("\n")


def has_frontmatter(text: str) -> bool:
    return text.startswith("---")


def make_frontmatter(title: str) -> str:
    safe = title.replace('"', '\\"')
    return f'---\ntitle: "{safe}"\n---\n\n'


# ---------------- PROCESSING ---------------- #

def process_file(path: Path):
    # Rename .md to .mdx first
    original_path = path
    if path.suffix == ".md":
        new_path = path.with_suffix(".mdx")
        path.rename(new_path)
        path = new_path
        print(f"[rename] {original_path} -> {path}")

    text = path.read_text(encoding="utf-8")

    if has_frontmatter(text):
        print(f"[skip]   {path} (has frontmatter)")
        return

    title, body = extract_h1(text)
    if not title:
        print(f"[skip]   {path} (no H1)")
        return

    frontmatter = make_frontmatter(title)
    new_text = frontmatter + body
    path.write_text(new_text, encoding="utf-8")

    print(f"[ok]     {path} (added title: {title})")


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_docs.py <path-to-docs-root>")
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"[error] Path not found: {root}")
        sys.exit(1)

    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md", ".mdx"}:
            process_file(p)


if __name__ == "__main__":
    main()