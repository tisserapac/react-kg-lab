"""Step 2: import one of the app's knowledge graphs into Memgraph.

The graphs were extracted from the movie-watchlist app by the research
pipeline and exported as CYPHERL: one Cypher statement per line. Importing
means running those statements one by one.

Only one graph is loaded at a time: the import first DELETES EVERYTHING in the
Memgraph you connect to.

    uv run python 02_import_graph.py movie-watchlist   # the full app (hooks, context, routes)
    uv run python 02_import_graph.py lab-solution      # the small lab version
"""
import argparse
import sys
import time

from kglab import memgraph, settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("graph", choices=["movie-watchlist", "lab-solution"])
    parser.add_argument("--app", help="path to the movie-watchlist repo (default ../movie-watchlist)")
    parser.add_argument("--yes", action="store_true", help="do not ask before deleting the current graph")
    args = parser.parse_args()

    dump = settings.app_dir(args.app) / "knowledge_graph" / args.graph / "full_dump.cypherl"
    if not dump.is_file():
        sys.exit(f"Not found: {dump}")
    statements = [s.strip() for s in dump.read_text(encoding="utf-8").splitlines() if s.strip()]

    driver = memgraph.connect()
    _, rows = memgraph.run(driver, "MATCH (n) RETURN count(n)")
    if rows[0][0] and not args.yes:
        answer = input(f"Memgraph at {settings.MEMGRAPH_URI} holds {rows[0][0]} nodes. Delete them all? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            sys.exit("Nothing changed.")
    memgraph.run(driver, "MATCH (n) DETACH DELETE n")

    print(f"Importing {len(statements)} statements from {dump.name} ...")
    start, errors = time.perf_counter(), 0
    with driver.session() as session:
        for statement in statements:
            try:
                session.run(statement).consume()
            except Exception as e:  # e.g. an index that already exists
                errors += 1
                print(f"  skipped: {str(e).splitlines()[0][:100]}")
    print(f"Done in {time.perf_counter() - start:.1f} s ({errors} statements skipped).\n")

    cols, rows = memgraph.run(driver, "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS nodes ORDER BY nodes DESC")
    print(memgraph.table(cols, rows), "\n")
    cols, rows = memgraph.run(
        driver, "MATCH ()-[r]->() RETURN type(r) AS relationship, count(*) AS count ORDER BY count DESC"
    )
    print(memgraph.table(cols, rows))
    print("\nOpen Memgraph Lab (http://localhost:3000) to see the graph, or run step 3.")
    driver.close()


if __name__ == "__main__":
    main()
