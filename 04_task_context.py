"""Step 4: build a context block for a coding task from the knowledge graph.

For task D2 or D3 of the movie-watchlist app this script
  1. reads the task (its spec) from ../movie-watchlist/tasks/<task>.yaml,
  2. runs the task's Cypher queries (queries/<task>.cypher) on the graph,
  3. writes a Markdown context block: the spec, each query's findings as a
     table, and the full source of every file a query returned in a `file` column.

That block is what you would put in front of an LLM, instead of the whole
project, to ask it to do the task.

    uv run python 04_task_context.py D2
    uv run python 04_task_context.py D3 --print     # also print the block

Compare your block with the research pipeline's, in
../movie-watchlist/tasks/contexts/<task>_kg_augmented_context.md
"""
import argparse
import sys

import yaml

from kglab import memgraph, settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task", choices=["D2", "D3"])
    parser.add_argument("--app", help="path to the movie-watchlist repo (default ../movie-watchlist)")
    parser.add_argument("--print", action="store_true", help="print the context block too")
    args = parser.parse_args()

    app = settings.app_dir(args.app)
    task = yaml.safe_load((app / "tasks" / f"{args.task}.yaml").read_text(encoding="utf-8"))
    queries = memgraph.load_queries(settings.QUERIES_DIR / f"{args.task}.cypher")

    driver = memgraph.connect()
    _, rows = memgraph.run(driver, "MATCH (h:Custom_Hook) RETURN count(h)")
    if not rows[0][0]:
        sys.exit("The graph in Memgraph has no custom hooks: import the full app first:\n"
                 "  uv run python 02_import_graph.py movie-watchlist")

    parts = [
        f"# Context for task {args.task} ({task['task_type']})",
        "## Task",
        task["spec"].strip(),
        "## What the knowledge graph says",
    ]
    files: list[str] = []
    print(f"Task {args.task}: running {len(queries)} queries\n")
    for q in queries:
        cols, rows = memgraph.run(driver, q.text)
        print(f"  {q.name:<28} {len(rows)} rows")
        findings = memgraph.table(cols, rows, markdown=True) if rows else "(nothing found)"
        parts.append(f"### {q.name}\n\n_{q.why}_\n\n{findings}")
        if "file" in cols:
            i = cols.index("file")
            files += [row[i] for row in rows if row[i] and row[i] not in files]
    driver.close()

    parts.append("## Source files")
    for f in files:
        lang = "jsx" if f.endswith("x") else "js"
        parts.append(f"### `{f}`\n\n```{lang}\n{(app / f).read_text(encoding='utf-8').rstrip()}\n```")

    block = "\n\n".join(parts) + "\n"
    out = settings.OUTPUT_DIR / f"{args.task}_context.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(block, encoding="utf-8")
    print(f"\nWrote {out.relative_to(settings.REPO_ROOT)}: {len(files)} source files, "
          f"{len(block)} characters (about {len(block) // 4} tokens).")
    research = app / "tasks" / "contexts" / f"{args.task}_kg_augmented_context.md"
    if research.is_file():
        size = len(research.read_text(encoding="utf-8"))
        print(f"Compare with the research pipeline's block: {research.relative_to(app.parent)} "
              f"({size} characters, about {size // 4} tokens).")
    if args.print:
        print("\n" + block)


if __name__ == "__main__":
    main()
