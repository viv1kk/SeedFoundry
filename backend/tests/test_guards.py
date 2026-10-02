"""Cheap guards copied from Seed v0.1's test_rehearsal.py (seed-reuse-notes.md §2.7):
no URL in the code names a host other than this machine (NFR-2), and no
model or LLM library is a dependency (D-1)."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCES = [
    ROOT / "run.py",
    ROOT / "run.ps1",
    ROOT / "backend" / "seedfoundry",
    ROOT / "frontend" / "index.html",
    ROOT / "frontend" / "vite.config.ts",
    ROOT / "frontend" / "src",
]
SOURCE_SUFFIXES = {".py", ".ps1", ".ts", ".js", ".vue", ".html", ".css", ".json", ".md"}

LOCAL_HOSTS = {"127.0.0.1", "localhost"}
# XML namespace names (for example in inline SVG) look like URLs but are never fetched.
NAMESPACE_HOSTS = {"www.w3.org"}

URL = re.compile(r"\b(?:https?|wss?)://([^/\s'\"`:)]*)")

MODEL_LIBRARIES = re.compile(
    r"^(openai|anthropic|@anthropic-ai/.*|langchain.*|@langchain/.*|llama.*|transformers|torch|tensorflow"
    r"|huggingface.*|@huggingface/.*|sentence-transformers|cohere.*|mistralai|@mistralai/.*|google-generativeai"
    r"|google-genai|@google/genai|@google/generative-ai|ollama|litellm|tiktoken|groq.*|replicate|vllm"
    r"|onnxruntime.*|ai|@ai-sdk/.*)$",
    re.IGNORECASE,
)


def source_files() -> list[Path]:
    found = []
    for path in SOURCES:
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            found += [p for p in path.rglob("*") if p.suffix in SOURCE_SUFFIXES and "__pycache__" not in p.parts]
    return found


def test_sources_are_scanned():
    names = {p.name for p in source_files()}
    assert {"run.py", "main.py", "vite.config.ts", "main.ts"} <= names


def test_no_url_names_a_host_other_than_this_machine():
    offenders = []
    for path in source_files():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for host in URL.findall(line):
                # A templated host ({BACKEND_HOST}, ${host}) is built from config.py, which is checked here too.
                if host and host not in LOCAL_HOSTS | NAMESPACE_HOSTS and not host.startswith(("{", "$")):
                    offenders.append(f"{path.relative_to(ROOT)}:{line_number}: {host}")
    assert offenders == []


def python_dependencies() -> set[str]:
    project = tomllib.loads((ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8"))
    declared = project["project"]["dependencies"] + [
        d for group in project.get("dependency-groups", {}).values() for d in group if isinstance(d, str)
    ]
    names = {re.split(r"[\s<>=!~\[;]", d, maxsplit=1)[0] for d in declared}
    lock = tomllib.loads((ROOT / "backend" / "uv.lock").read_text(encoding="utf-8"))
    names |= {package["name"] for package in lock.get("package", [])}
    return names


def node_dependencies() -> set[str]:
    package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    names = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    lock = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    names |= {key.rsplit("node_modules/", 1)[-1] for key in lock.get("packages", {}) if key}
    return names


def test_dependency_lists_are_read():
    assert {"fastapi", "uvicorn", "pytest"} <= python_dependencies()
    assert {"vue", "vite", "vitest"} <= node_dependencies()


def test_no_model_or_llm_library_is_a_dependency():
    found = sorted(n for n in python_dependencies() | node_dependencies() if MODEL_LIBRARIES.match(n))
    assert found == []
