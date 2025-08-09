import tempfile
import subprocess
from pathlib import Path


class LatexCompilationError(Exception):
    """Raised when LaTeX compilation fails."""


def _strip_code_fences(text: str) -> str:
    """Remove surrounding markdown code fences if present."""
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        # remove opening fence with optional language
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 : -3]
    return stripped


def _ensure_document_structure(body: str) -> str:
    """
    If the provided LaTeX is not a full document, wrap it in a minimal template.
    """
    text = body.strip()
    if "\\documentclass" in text and "\\begin{document}" in text:
        return text

    # If end marker exists but no documentclass, still wrap
    content = text
    template = r"""
\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\geometry{margin=1in}
\begin{document}
% Auto-wrapped by server because the input LaTeX was not a full document.
% Edit your LaTeX freely; the server will compile whatever you type.
% ---- Content starts ----
%
""".strip()

    closing = "\n\\end{document}\n"
    return template + "\n" + content + closing


def preprocess_latex(latex_source: str) -> str:
    """Normalize incoming LaTeX for compilation."""
    def _sanitize_for_tectonic(text: str) -> str:
        # Remove pdfTeX-specific primitives that fail under XeTeX (tectonic)
        filtered_lines = []
        for raw in text.splitlines():
            line = raw
            if "\\input{glyphtounicode}" in line:
                # Not needed for XeTeX
                continue
            if "\\pdfgentounicode" in line:
                # pdfTeX primitive
                continue
            filtered_lines.append(line)
        return "\n".join(filtered_lines)

    without_fences = _strip_code_fences(latex_source)
    sanitized = _sanitize_for_tectonic(without_fences)
    normalized = _ensure_document_structure(sanitized)
    return normalized


def compile_latex_to_pdf(latex_source: str) -> bytes:
    """
    Compile LaTeX source to PDF using the `tectonic` engine.

    Returns the compiled PDF bytes if successful, otherwise raises
    LatexCompilationError with stderr/stdout from the compiler.
    """
    # Safety: keep work inside a temp directory; no shell execution
    with tempfile.TemporaryDirectory(prefix="latex_build_") as work_dir:
        work_path = Path(work_dir)
        tex_path = work_path / "resume.tex"
        pdf_path = work_path / "resume.pdf"

        preprocessed = preprocess_latex(latex_source)
        tex_path.write_text(preprocessed, encoding="utf-8")

        # Run tectonic. The -o flag sets output dir. We keep logs for diagnostics.
        # Note: tectonic returns non-zero on errors; capture output for error reporting.
        process = subprocess.run(
            [
                "tectonic",
                str(tex_path),
                "-o",
                str(work_path),
                "-Z",
                "continue-on-errors",
            ],
            cwd=work_dir,
            check=False,
            capture_output=True,
            text=True,
        )

        if process.returncode != 0 or not pdf_path.exists():
            message = "LaTeX compilation failed."
            detail = (process.stdout or "") + "\n" + (process.stderr or "")
            raise LatexCompilationError(f"{message}\n{detail}")

        return pdf_path.read_bytes()

