#!/usr/bin/env python3
import sys
from pathlib import Path

import markdown
from rst_in_md.extension import RestructuredTextInMarkdownPreProcessor


def process_file(path: Path):
    text = path.read_text(encoding="utf-8")

    # Create a dummy Markdown instance – the preprocessor expects this
    md = markdown.Markdown()

    # Use rst-in-md's preprocessor directly
    pre = RestructuredTextInMarkdownPreProcessor(md)
    new_lines = pre.run(text.splitlines())
    new_text = "\n".join(new_lines)

    path.write_text(new_text, encoding="utf-8")
    print(f"Processed {path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_rst_in_md.py <path-to-file-or-folder>")
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"Path not found: {root}")
        sys.exit(1)

    if root.is_file() and root.suffix in {".md", ".mdx"}:
        process_file(root)
        return

    # Walk directory tree and process all md/mdx files
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".mdx"}:
            process_file(p)


if __name__ == "__main__":
    main()