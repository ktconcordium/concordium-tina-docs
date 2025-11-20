import re
import json
from pathlib import Path

VARIABLES_RST = Path("docs/variables.rst")      # adjust path
OUTPUT_JSON = Path("src/content/variables.json")  # where Tina/Next can import it

pattern = re.compile(r"\.\.\s+\|([^|]+)\|\s+replace::\s+(.*)")

def main():
    mapping = {}

    text = VARIABLES_RST.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        key = m.group(1).strip()
        value = m.group(2).strip()
        mapping[key] = value

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(mapping)} variables to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()