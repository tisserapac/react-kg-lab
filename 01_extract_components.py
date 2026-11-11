"""Step 1: extract React function components with few-shot prompting.

For each .js/.jsx file of the movie-watchlist app, the LLM gets:
  - instructions (prompts/function_components/system.md),
  - a few worked examples (prompts/function_components/examples/): an example
    file as a user turn, the JSON we expect as the assistant's reply,
  - then the real file.
It replies with JSON, which we check against a schema (pydantic) and save.

    uv run python 01_extract_components.py                      # every file in src/
    uv run python 01_extract_components.py --file src/components/MovieCard.jsx
    uv run python 01_extract_components.py --zero-shot          # no examples: compare!
    uv run python 01_extract_components.py --show-prompt --file src/App.jsx
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from kglab import llm, settings

PROMPT_DIR = settings.PROMPTS_DIR / "function_components"
SKIP_DIRS = {"__tests__", "node_modules", "dist"}


# ── the JSON shape we ask for (same fields as in prompts/.../system.md) ────

class Hook(BaseModel):
    name: str
    source: str


class Component(BaseModel):
    name: str
    syntax: Literal["function", "arrow"]
    exportType: Literal["default", "named", "none"]
    props: list[str] = []
    hooks: list[Hook] = []


class FileComponents(BaseModel):
    components: list[Component]


# ── building the prompt ─────────────────────────────────────────────────────

def user_turn(path: str, code: str) -> dict:
    lang = "jsx" if path.endswith("x") else "js"
    return {"role": "user", "content": f"File: {path}\n\n```{lang}\n{code}\n```"}


def few_shot_turns() -> list[dict]:
    """Each example is a pair of files: <name>.js(x) and <name>.json."""
    turns = []
    for answer in sorted((PROMPT_DIR / "examples").glob("*.json")):
        source = next(p for p in answer.parent.glob(answer.stem + ".*") if p.suffix != ".json")
        turns.append(user_turn(f"examples/{source.name}", source.read_text(encoding="utf-8")))
        turns.append({"role": "assistant", "content": answer.read_text(encoding="utf-8").strip()})
    return turns


def build_prompt(rel_path: str, code: str, zero_shot: bool) -> tuple[str, list[dict]]:
    system = (PROMPT_DIR / "system.md").read_text(encoding="utf-8")
    examples = [] if zero_shot else few_shot_turns()
    return system, examples + [user_turn(rel_path, code)]


# ── reading the reply ───────────────────────────────────────────────────────

def parse_reply(text: str) -> FileComponents:
    """Take the JSON object out of the reply (models sometimes wrap it in ```json)."""
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("no JSON object in the reply")
    return FileComponents.model_validate(json.loads(match.group(0)))


def extract(app: Path, rel_path: str, zero_shot: bool) -> dict:
    code = (app / rel_path).read_text(encoding="utf-8")
    system, turns = build_prompt(rel_path, code, zero_shot)
    reply = ""
    try:
        reply = llm.complete(system, turns)
        components = parse_reply(reply).model_dump()["components"]
        return {"file": rel_path, "components": components}
    except (ValueError, ValidationError, RuntimeError) as e:
        # keep the raw reply, so you can see what the model actually said
        return {"file": rel_path, "error": str(e).splitlines()[0], "reply": reply}


def source_files(app: Path) -> list[str]:
    files = []
    for path in sorted((app / "src").rglob("*")):
        rel = path.relative_to(app)
        if path.suffix in {".js", ".jsx"} and not SKIP_DIRS & set(rel.parts) and ".test." not in path.name:
            files.append(rel.as_posix())
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", help="path to the movie-watchlist repo (default ../movie-watchlist)")
    parser.add_argument("--file", action="append", help="only this file (path inside the app); repeatable")
    parser.add_argument("--zero-shot", action="store_true", help="leave out the examples")
    parser.add_argument("--show-prompt", action="store_true", help="print the prompt and stop (no LLM call)")
    args = parser.parse_args()

    app = settings.app_dir(args.app)
    files = args.file or source_files(app)
    for f in files:
        if not (app / f).is_file():
            sys.exit(f"No such file in the app: {f}")

    if args.show_prompt:
        system, turns = build_prompt(files[0], (app / files[0]).read_text(encoding="utf-8"), args.zero_shot)
        print("=== SYSTEM ===\n" + system)
        for turn in turns:
            print(f"=== {turn['role'].upper()} ===\n{turn['content']}\n")
        return

    llm.check_ready()
    mode = "zero-shot" if args.zero_shot else f"few-shot ({len(few_shot_turns()) // 2} examples)"
    print(f"Extracting function components from {len(files)} files with {settings.LLM_MODEL}, {mode}\n")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda f: extract(app, f, args.zero_shot), files))

    out_dir = settings.OUTPUT_DIR / ("components_zero_shot" if args.zero_shot else "components")
    for r in results:
        print(f"── {r['file']}")
        if "error" in r:
            print(f"   ERROR: {r['error']}\n   reply: {r['reply'][:300]!r}\n")
            continue
        print(json.dumps({"components": r["components"]}, indent=2), "\n")
        target = out_dir / (r["file"] + ".json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")

    found = [(r["file"], c) for r in results if "components" in r for c in r["components"]]
    errors = [r for r in results if "error" in r]
    print(f"Found {len(found)} function components in {len(files)} files ({len(errors)} errors):")
    for file, c in found:
        hooks = ", ".join(h["name"] for h in c["hooks"]) or "-"
        print(f"  {c['name']:<16} {file:<34} props: {', '.join(c['props']) or '-'}  hooks: {hooks}")
    all_path = out_dir.with_suffix(".json")
    all_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved: {out_dir.relative_to(settings.REPO_ROOT)}/ (one JSON per file) and {all_path.name}")


if __name__ == "__main__":
    main()
