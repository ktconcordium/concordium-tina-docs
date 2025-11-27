#!/usr/bin/env python3
import re
from pathlib import Path
import sys

def has_frontmatter_title(path: Path) -> bool:
    """
    Returns True if the file starts with:
    ---
    title: "Something"
    ---
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False

    if not text.startswith("---"):
        return False

    # Split frontmatter region
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False  # malformed or missing closing ---

    fm = parts[1]  # content between the first two '---'

    # Look for title: "..."
    return bool(re.search(r'^\s*title\s*:\s*["\'].*["\']\s*$', fm, re.MULTILINE))


def main():
    if len(sys.argv) < 2:
        print("Usage: python list_missing_titles.py <docs-root>")
        sys.exit(1)

    docs_root = Path(sys.argv[1]).resolve()
    if not docs_root.exists():
        print(f"Error: folder not found: {docs_root}")
        sys.exit(1)

    missing = []

    for p in docs_root.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".mdx"}:
            if not has_frontmatter_title(p):
                missing.append(str(p))

    print("\n=== Files missing MDX frontmatter title ===")
    if not missing:
        print("All files OK! 🎉")
    else:
        for f in missing:
            print(f)

    print(f"\nTotal: {len(missing)} files missing title\n")


if __name__ == "__main__":
    main()