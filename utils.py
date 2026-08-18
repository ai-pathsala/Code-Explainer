"""
utils.py
--------
Small helper functions used by app.py:
- language detection from file extension
- splitting long code into digestible chunks for line-by-line explanation
- building a downloadable Markdown report
"""

EXTENSION_LANG_MAP = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".java": "java", ".c": "c", ".h": "c", ".cpp": "cpp",
    ".hpp": "cpp", ".cs": "csharp", ".go": "go", ".rs": "rust", ".rb": "ruby",
    ".php": "php", ".html": "html", ".css": "css", ".sql": "sql", ".sh": "bash",
    ".kt": "kotlin", ".swift": "swift", ".r": "r", ".m": "matlab", ".scala": "scala",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".dart": "dart", ".lua": "lua",
    ".pl": "perl", ".xml": "xml", ".txt": "text",
}


def detect_language(filename: str) -> str:
    filename = filename.lower()
    for ext, lang in EXTENSION_LANG_MAP.items():
        if filename.endswith(ext):
            return lang
    return "text"


def number_lines(code: str) -> list[str]:
    """Returns code lines, 1-indexed, for stable reference by the LLM and UI."""
    return code.splitlines()


def chunk_code(code: str, chunk_size: int = 30) -> list[tuple[int, int, str]]:
    """
    Splits code into (start_line, end_line, chunk_text) tuples of ~chunk_size lines.
    Line numbers are 1-indexed and continuous, so explanations can be reassembled
    in original order.
    """
    lines = code.splitlines()
    chunks = []
    i = 0
    n = len(lines)
    while i < n:
        end = min(i + chunk_size, n)
        chunk_text = "\n".join(lines[i:end])
        chunks.append((i + 1, end, chunk_text))
        i = end
    return chunks or [(1, 0, "")]


def build_markdown_report(
    filename: str,
    language: str,
    code: str,
    line_explanations: list[dict],
    complexity: str | None,
    bugs: str | None,
) -> str:
    """Assembles everything into one Markdown document for download."""
    parts = [f"# Code Explanation Report: `{filename}`\n", f"**Language:** {language}\n"]

    parts.append("## Line-by-Line Explanation\n")
    for block in line_explanations:
        start, end = block.get("start_line"), block.get("end_line")
        snippet = block.get("code", "")
        explanation = block.get("explanation", "")
        line_label = f"Lines {start}-{end}" if start != end else f"Line {start}"
        parts.append(f"### {line_label}")
        parts.append(f"```{language}\n{snippet}\n```")
        parts.append(f"{explanation}\n")

    if complexity:
        parts.append("## Complexity Analysis\n")
        parts.append(complexity + "\n")

    if bugs:
        parts.append("## Potential Bugs & Improvements\n")
        parts.append(bugs + "\n")

    parts.append("## Full Original Source\n")
    parts.append(f"```{language}\n{code}\n```")

    return "\n".join(parts)
