#!/usr/bin/env python3
"""
Convert Sphinx/MyST-flavoured markdown into TinaCMS-friendly MDX.

What it does:
- Loads variables from a variables.rst file (.. |name| replace:: value)
- Loads substitutions from frontmatter `substitutions:` and uses them for {{ var }}
- Replaces:
    - {{ var }} -> value
    - |var|     -> value
- Converts RST-style inline links:
    `text <https://example.com>`__ -> [text](https://example.com)
- Converts {term}`label<slug>` / {term}`label`
  and :term:`label<slug>` / :term:`label`
  to glossary links:
    [label](/docs/glossary.html#slugifiedid)
- Builds an index of internal labels and converts:
    :ref:`text<label>` -> [text](/docs/...#label)
    :ref:`label`       -> [label](/docs/...#label)
  or, if unresolved, [text](#label)
- Removes ```{toctree} ... ``` blocks
- Converts MyST admonitions:

    :::{note}
    text
    :::

  into:

    <Callout variant="info">
    text
    </Callout>

- Converts ```{eval-rst} .. dropdown:: title ... ``` blocks into the Tina
  accordion embed:

    <accordion
      heading="Title"
      docText={<>
      ...
      </>}
      image=""
      fullWidth={false}
    />

  and turns simple '.. image::' directives inside into Markdown images.

- Converts MyST image fences:

    ```{image} path
    :alt: text
    :width: ...
    ```

  into:

    ![text](path)

Limitations:
- Dropdown content parsing is "good enough", not a full RST parser.
- Any weird/unexpected eval-rst blocks are dropped or left untouched.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Match, Tuple


# ----------------- VARIABLES ----------------- #

def load_variables(variables_path: Path) -> Dict[str, str]:
    """
    Parse a variables.rst file with lines like:
    .. |cryptox| replace:: Concordium Wallet
    Returns dict: {"cryptox": "Concordium Wallet", ...}
    """
    mapping: Dict[str, str] = {}
    if not variables_path.exists():
        print(f"[warn] variables.rst not found at {variables_path}, skipping variables.rst substitution")
        return mapping

    text = variables_path.read_text(encoding="utf-8")
    # Match: .. |name| replace:: value
    pattern = re.compile(r"^\s*\.\.\s+\|([^|]+)\|\s+replace::\s+(.*)$", re.MULTILINE)
    for m in pattern.finditer(text):
        name = m.group(1).strip()
        value = m.group(2).strip()
        mapping[name] = value
    print(f"[info] Loaded {len(mapping)} variables from {variables_path}")
    return mapping


def substitute_variables(text: str, var_map: Dict[str, str]) -> str:
    """
    Replace:
      {{ var }} and |var|
    using var_map.
    """

    def repl_double_braces(m: Match[str]) -> str:
        key = m.group(1).strip()
        return var_map.get(key, m.group(0))

    def repl_pipes(m: Match[str]) -> str:
        key = m.group(1).strip()
        return var_map.get(key, m.group(0))

    # {{ var }}
    text = re.sub(r"\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}", repl_double_braces, text)
    # |var|
    text = re.sub(r"\|([a-zA-Z0-9_-]+)\|", repl_pipes, text)
    return text


# ----------------- FRONTMATTER HANDLING ----------------- #

def split_frontmatter(text: str) -> Tuple[str, str]:
    """
    If the file starts with frontmatter delimited by --- ... ---,
    split into (frontmatter, body). Otherwise, ("" , text).
    """
    if not text.startswith("---"):
        return "", text

    lines = text.splitlines(keepends=True)
    if not lines:
        return "", text

    # first line is '---', find the next '---'
    second_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            second_idx = i
            break

    if second_idx is None:
        # malformed frontmatter, treat whole file as body
        return "", text

    frontmatter = "".join(lines[: second_idx + 1])
    body = "".join(lines[second_idx + 1 :])
    return frontmatter, body


def extract_substitutions_from_frontmatter(frontmatter: str) -> Dict[str, str]:
    """
    Very specific parser for a frontmatter block like:

    ---
    substitutions:
      menu: |-
        ```{image} ../images/foo.png
        :alt: menu icon
        :width: 50px
        ```
      activity: |-
        ...
    ---

    Returns a map such as:
      {"menu": "![menu icon](../images/foo.png)", ...}
    """
    if not frontmatter:
        return {}

    lines = frontmatter.splitlines()
    var_map: Dict[str, str] = {}

    inside_subst = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not inside_subst:
            if stripped == "substitutions:":
                inside_subst = True
            i += 1
            continue

        # If we see an unindented non-empty line, we left the substitutions block
        if stripped and not line.startswith("  "):
            break

        # Match "  key: |-"
        m = re.match(r"^\s{2}([a-zA-Z0-9_-]+):\s*\|\-\s*$", line)
        if m:
            key = m.group(1)
            j = i + 1
            block_lines: List[str] = []
            # Collect indented block (>= 4 spaces)
            while j < len(lines):
                l2 = lines[j]
                if l2.strip() == "---":
                    break
                if re.match(r"^\s{4,}", l2):
                    block_lines.append(l2[4:])
                    j += 1
                else:
                    # another key or out of substitutions
                    break

            block_text = "\n".join(block_lines)

            # Find MyST image directive inside this block
            mimg = re.search(
                r"```{image}\s+([^\s]+)\s*\n([\s\S]*?)```",
                block_text,
                re.MULTILINE,
            )
            if mimg:
                path = mimg.group(1).strip()
                options = mimg.group(2)
                malt = re.search(r":alt:\s+(.*)", options)
                alt = malt.group(1).strip() if malt else ""
                var_map[key] = f"![{alt}]({path})"

            i = j
        else:
            i += 1

    if var_map:
        print(f"[info] Extracted {len(var_map)} substitutions from frontmatter")
    return var_map


# ----------------- RST INLINE LINKS ----------------- #

def convert_rst_links(text: str) -> str:
    """
    Convert RST-style inline links of the form:

      `dApps <https://en.wikipedia.org/wiki/Decentralized_application>`__

    (or single underscore) into standard markdown:

      [dApps](https://en.wikipedia.org/wiki/Decentralized_application)
    """

    def repl(m: Match[str]) -> str:
        label = m.group(1).strip()
        url = m.group(2).strip()
        return f"[{label}]({url})"

    pattern = re.compile(r"`([^`]+?)\s*<([^>]+)>`_{1,2}")
    return pattern.sub(repl, text)


# ----------------- {term} / :term: ROLES → GLOSSARY ----------------- #

def _slugify_glossary_id(s: str) -> str:
    """
    Produce glossary anchors such as 'identityprovider'
    from 'Identity provider', etc.
    """
    s = s.lower()
    return re.sub(r"[^a-z0-9]", "", s)


def _convert_single_term(inner: str) -> str:
    """
    Convert the inside of a term role:

      "identity provider"
      "Label<Some Glossary Title>"

    into a Markdown link string:
      [Label](/docs/glossary.html#slugifiedid)
    """
    if "<" in inner and ">" in inner:
        mm = re.match(r"([^<]+)<([^>]+)>", inner)
        if mm:
            label, slug_src = mm.groups()
            label = label.strip()
            slug_src = slug_src.strip()
        else:
            label = inner.strip()
            slug_src = label
    else:
        label = inner.strip()
        slug_src = label

    slug = _slugify_glossary_id(slug_src)
    return f"[{label}](/docs/glossary.html#{slug})"


def convert_term_roles(text: str) -> str:
    """
    Convert both MyST and classic Sphinx term roles into glossary links:

      {term}`identity provider`
      {term}`ConcordiumBFT<Concordium Byzantine Fault Tolerance>`

      :term:`identity provider`
      :term:`ConcordiumBFT<Concordium Byzantine Fault Tolerance>`

    → [identity provider](/docs/glossary.html#identityprovider)
    """

    # {term}`...`
    def repl_curly(m: Match[str]) -> str:
        inner = m.group(1)
        return _convert_single_term(inner)

    text = re.sub(r"\{term\}`([^`]+)`", repl_curly, text)

    # :term:`...`
    def repl_colon(m: Match[str]) -> str:
        inner = m.group(1)
        return _convert_single_term(inner)

    text = re.sub(r":term:`([^`]+)`", repl_colon, text)

    return text


# ----------------- LABEL INDEX FOR :ref: ----------------- #

def build_label_index(docs_root: Path) -> Dict[str, str]:
    """
    Scan all .md/.mdx/.rst files and collect:
    - '.. _label:' style labels
    - '(label)=' MyST style labels
    - Markdown headings with explicit IDs: '# Text {#label}'

    Returns dict: {label: "/docs/path/to/file#label"}
    """
    index: Dict[str, str] = {}

    for path in docs_root.rglob("*"):
        if not (path.is_file() and path.suffix in {".md", ".mdx", ".rst"}):
            continue

        # Build a URL-ish path relative to content/docs
        rel_part = str(path).split("content/docs/")[-1]
        rel_part = rel_part.replace("\\", "/")
        rel_no_ext = rel_part.rsplit(".", 1)[0]  # remove extension
        base_url = f"/docs/{rel_no_ext}"

        text = path.read_text(encoding="utf-8")

        # 1. RST style: .. _label:
        for m in re.finditer(r"^\.\.\s*_([a-zA-Z0-9_-]+):\s*$", text, re.MULTILINE):
            label = m.group(1).strip()
            index[label] = f"{base_url}#{label}"

        # 2. MyST style: (label)=
        for m in re.finditer(r"^$begin:math:text$\(\[a\-zA\-Z0\-9\_\-\]\+\)$end:math:text$=", text, re.MULTILINE):
            label = m.group(1).strip()
            index[label] = f"{base_url}#{label}"

        # 3. Markdown heading style: # Title {#label}
        for m in re.finditer(r"\{#([a-zA-Z0-9_-]+)\}", text):
            label = m.group(1).strip()
            index[label] = f"{base_url}#{label}"

    print(f"[info] Indexed {len(index)} internal labels for :ref:")
    return index


def convert_ref_roles(text: str, label_index: Dict[str, str]) -> str:
    """
    Convert :ref:`text<label>` → [text](resolved_url)
            :ref:`label`      → [label](resolved_url) when possible.

    If the label cannot be resolved from label_index, fall back to a
    local anchor:

      [text](#label)

    so we don't lose the link completely.
    """

    def repl(m: Match[str]) -> str:
        inner = m.group(1)
        if "<" in inner and ">" in inner:
            mm = re.match(r"([^<]+)<([^>]+)>", inner)
            if not mm:
                return m.group(0)
            text_part, label = mm.groups()
            text_part = text_part.strip()
            label = label.strip()
        else:
            text_part = inner.strip()
            label = inner.strip()

        dest = label_index.get(label)
        if dest:
            # Label resolved from another file
            return f"[{text_part}]({dest})"

        # Fallback: assume a local anchor on the same page: #label
        return f"[{text_part}](#{label})"

    return re.sub(r":ref:`([^`]+)`", repl, text)


# ----------------- TOCTREE ----------------- #

def remove_toctree_blocks(text: str) -> str:
    """
    Remove ```{toctree} ... ``` blocks completely.
    They are only for Sphinx navigation.
    """
    pattern = re.compile(r"```{toctree}[\s\S]*?```", re.MULTILINE)
    return pattern.sub("", text)


# ----------------- ADMONITIONS ----------------- #

ADMONITION_MAP = {
    "note": "info",
    "warning": "warning",
    "caution": "warning",
    "tip": "idea",
    "important": "info",
}


def convert_admonitions(text: str) -> str:
    """
    Convert MyST admonitions:

      :::{note}
      text
      :::

    to:

      <Callout variant="info">
      text
      </Callout>
    """
    pattern = re.compile(
        r":::\{?(note|warning|tip|important|caution)\}?\s*\n([\s\S]*?)\n:::",
        re.IGNORECASE,
    )

    def repl(m: Match[str]) -> str:
        kind = m.group(1).lower()
        body = m.group(2).strip("\n")
        variant = ADMONITION_MAP.get(kind, "info")
        return f'<Callout variant="{variant}">\n\n{body}\n\n</Callout>'

    return pattern.sub(repl, text)


# ----------------- DROPDOWN (eval-rst) → accordion ----------------- #

def dedent_block(lines: List[str]) -> List[str]:
    """
    Remove common leading indentation from a block of lines.
    """
    indents: List[int] = []
    for line in lines:
        if line.strip():
            spaces = len(line) - len(line.lstrip(" "))
            indents.append(spaces)
    if not indents:
        return lines
    min_indent = min(indents)
    return [line[min_indent:] if len(line) >= min_indent else line for line in lines]


def convert_rst_images(lines: List[str]) -> List[str]:
    """
    Convert simple RST image directives:

      .. image:: path
         :alt: text
         :width: 50%

    to Markdown images:

      ![text](path)
    """
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        img_match = re.match(r"\s*\.\.\s+image::\s+(.+)$", line)
        if img_match:
            path = img_match.group(1).strip()
            alt = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if re.match(r"\s*:\w+:", next_line):
                    alt_match = re.match(r"\s*:alt:\s+(.*)$", next_line)
                    if alt_match:
                        alt = alt_match.group(1).strip()
                    j += 1
                elif next_line.strip() == "":
                    j += 1
                else:
                    break
            out.append(f"![{alt}]({path})")
            i = j
        else:
            out.append(line)
            i += 1
    return out


def renumber_ordered_list(content: str) -> str:
    """
    Take markdown content and turn sequences of lines starting with '1. '
    into 1., 2., 3., ... so Tina doesn't render all as 1.

    We *don't* reset on blank lines, so lists separated by blank lines still
    count as a single logical list. We reset when we hit a heading or
    bullet list line.
    """
    lines = content.splitlines()
    out_lines: List[str] = []
    current_index = 0

    for line in lines:
        m = re.match(r"^(\s*)1\.\s+(.*)$", line)
        if m:
            indent, text = m.groups()
            current_index += 1
            out_lines.append(f"{indent}{current_index}. {text}")
        else:
            out_lines.append(line)
            stripped = line.strip()
            if stripped.startswith("#") or re.match(r"^[-*]\s+", stripped):
                # reset on headings or bullet lists
                current_index = 0

    return "\n".join(out_lines)


def convert_eval_rst_block(inner: str) -> str:
    """
    Convert the content of an ```{eval-rst} ... ``` block.

    We specifically handle '.. dropdown::' blocks and turn them into:

      <accordion
        heading="Title"
        docText={<>
        ...
        </>}
        image=""
        fullWidth={false}
      />

    Other eval-rst content is dropped with a comment.
    """
    # Drop include of variables file – we've already substituted variables.
    if ".. include::" in inner and "variables.rst" in inner:
        return ""

    if ".. dropdown::" not in inner:
        # Unknown eval-rst, keep as is or drop. Here we drop with a comment.
        return "<!-- dropped unknown eval-rst block -->"

    lines = inner.splitlines()

    # Find dropdown directive
    heading = "Details"
    content_lines: List[str] = []
    found = False
    for idx, line in enumerate(lines):
        m = re.match(r"\s*\.\.\s+dropdown::\s+(.*)$", line)
        if m:
            raw_heading = m.group(1).strip()
            heading = raw_heading
            content_lines = lines[idx + 1 :]
            found = True
            break

    if not found:
        return "<!-- malformed dropdown eval-rst block -->"

    # Dedent content
    content_lines = dedent_block(content_lines)
    # Convert RST image directives inside to markdown images
    content_lines = convert_rst_images(content_lines)

    # Strip leading/trailing blank lines
    while content_lines and content_lines[0].strip() == "":
        content_lines.pop(0)
    while content_lines and content_lines[-1].strip() == "":
        content_lines.pop()

    content = "\n".join(content_lines)

    # Convert RST ordered list markers "#." to Markdown "1."
    content = re.sub(r"^#\.\s+", "1. ", content, flags=re.MULTILINE)

    # Renumber 1. → 1., 2., 3., ...
    content = renumber_ordered_list(content)

    # Escape double quotes in heading so it’s safe inside "
    safe_heading = heading.replace('"', '\\"')

    # Build the Tina accordion JSX (lowercase, docText fragment)
    return (
        "<accordion\n"
        f'  heading="{safe_heading}"\n'
        "  docText={<>\n"
        f"{content}\n"
        "  </>}\n"
        '  image=""\n'
        "  fullWidth={false}\n"
        "/>"
    )


def convert_eval_rst_blocks(text: str) -> str:
    """
    Find ```{eval-rst} ... ``` fenced blocks and convert them.
    """
    pattern = re.compile(r"```{eval-rst}\s*\n([\s\S]*?)\n```", re.MULTILINE)

    def repl(m: Match[str]) -> str:
        inner = m.group(1)
        return convert_eval_rst_block(inner)

    return pattern.sub(repl, text)


# ----------------- MyST IMAGE FENCES → MARKDOWN IMAGES ----------------- #

def convert_myst_image_blocks(text: str) -> str:
    """
    Convert MyST image fences of the form:

      ```{image} ../images/foo.png
      :alt: some alt
      :width: 50%
      ```

    into:

      ![some alt](../images/foo.png)
    """

    pattern = re.compile(
        r"^(\s*)```{image}\s+([^\s]+)\s*\n([\s\S]*?)\n\1```",
        re.MULTILINE,
    )

    def repl(m: Match[str]) -> str:
        indent = m.group(1)
        path = m.group(2).strip()
        options = m.group(3)
        malt = re.search(r":alt:\s+(.*)", options)
        alt = malt.group(1).strip() if malt else ""
        return f"{indent}![{alt}]({path})"

    return pattern.sub(repl, text)


# ----------------- MAIN CONVERSION PIPELINE ----------------- #

def convert_text(text: str, var_map: Dict[str, str], label_index: Dict[str, str]) -> str:
    # 1. Substitute variables first so dropdown titles & bodies expand
    text = substitute_variables(text, var_map)

    # 2. Convert RST-style external links
    text = convert_rst_links(text)

    # 3. Convert {term} / :term: roles to glossary links
    text = convert_term_roles(text)

    # 4. Resolve :ref: roles using the label index
    text = convert_ref_roles(text, label_index)

    # 5. Remove toctree blocks
    text = remove_toctree_blocks(text)

    # 6. Convert eval-rst dropdowns -> accordion embed
    text = convert_eval_rst_blocks(text)

    # 7. Convert MyST image fences ```{image} ... ```
    text = convert_myst_image_blocks(text)

    # 8. Convert admonitions (:::{note} etc.)
    text = convert_admonitions(text)

    return text


def process_file(path: Path, global_var_map: Dict[str, str], label_index: Dict[str, str]):
    original = path.read_text(encoding="utf-8")

    # Split frontmatter and body
    frontmatter, body = split_frontmatter(original)

    # Extract substitutions from frontmatter and combine with global var map
    file_var_map = dict(global_var_map)
    file_var_map.update(extract_substitutions_from_frontmatter(frontmatter))

    converted_body = convert_text(body, file_var_map, label_index)
    converted = frontmatter + converted_body

    if converted != original:
        path.write_text(converted, encoding="utf-8")
        print(f"[ok] Converted {path}")
    else:
        print(f"[skip] No changes in {path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_sphinx_to_tina.py <path-to-docs-root> <path-to-variables.rst>")
        print("Example: python convert_sphinx_to_tina.py content/docs source/mainnet/variables.rst")
        sys.exit(1)

    docs_root = Path(sys.argv[1]).resolve()
    variables_path = Path(sys.argv[2]).resolve()

    if not docs_root.exists():
        print(f"[error] Docs root not found: {docs_root}")
        sys.exit(1)

    global_var_map = load_variables(variables_path)
    label_index = build_label_index(docs_root)

    for p in docs_root.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".mdx"}:
            process_file(p, global_var_map, label_index)


if __name__ == "__main__":
    main()