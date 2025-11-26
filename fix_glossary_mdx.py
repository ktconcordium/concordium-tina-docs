#!/usr/bin/env python3
from pathlib import Path
import re

# 👉 adjust this path if your glossary file lives elsewhere
GLOSSARY_PATH = Path(
    "content/docs/mainnet/docs/resources/glossary.mdx"
)

text = GLOSSARY_PATH.read_text(encoding="utf-8")

# 1) Remove MyST glossary wrapper
text = text.replace(":::{glossary}\n", "")
text = text.replace("\n:::\n", "\n")

lines = text.splitlines()
out = []

def looks_like_term(i: int) -> bool:
    """
    Detect RST glossary term blocks converted to MDX.
    """
    if i + 2 >= len(lines):
        return False
    line = lines[i].strip()
    if not line:
        return False
    # ignore markdown headings, blockquotes, lists, etc.
    if line.startswith(("#", ">", "[", "(", "---")):
        return False
    # expect blank line after term
    if lines[i + 1].strip() != "":
        return False
    # expect a definition starting with '>'
    if not lines[i + 2].lstrip().startswith(">"):
        return False
    return True


i = 0
while i < len(lines):
    line = lines[i]

    if looks_like_term(i):
        term = line.strip()
        out.append(f"###### {term}")   # ← smallest heading, no anchor
        i += 1
        continue

    # Remove leading '>' from definitions
    if line.lstrip().startswith(">"):
        stripped = line.lstrip()[1:]
        if stripped.startswith(" "):
            stripped = stripped[1:]
        out.append(stripped)
        i += 1
        continue

    out.append(line)
    i += 1

fixed = "\n".join(out)

# Fix math syntax
fixed = fixed.replace("{math}`\\alpha`", r"$\alpha$")

GLOSSARY_PATH.write_text(fixed, encoding="utf-8")

print("Glossary MDX cleaned ✔ (small headings, no anchors)")