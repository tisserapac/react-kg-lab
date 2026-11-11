"""Step 3: run the Cypher queries in queries/explore.cypher and print the results.

    uv run python 03_explore_graph.py              # all queries
    uv run python 03_explore_graph.py --list       # just their names
    uv run python 03_explore_graph.py 4 9          # only queries 4 and 9
    uv run python 03_explore_graph.py --file queries/my_queries.cypher

Write your own queries in a .cypher file in the same format and run them with --file.
"""
import argparse
from pathlib import Path

from kglab import memgraph, settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("numbers", nargs="*", help="which queries to run (the number at the start of the name)")
    parser.add_argument("--file", default=str(settings.QUERIES_DIR / "explore.cypher"))
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    queries = memgraph.load_queries(Path(args.file))
    if args.numbers:
        queries = [q for q in queries if q.name.split("-")[0] in args.numbers]
    if args.list:
        for q in queries:
            print(f"{q.name:<34} {q.why}")
        return

    driver = memgraph.connect()
    for q in queries:
        print(f"\n=== {q.name}\n    {q.why}\n")
        print("    " + q.text.replace("\n", "\n    ") + "\n")
        try:
            cols, rows = memgraph.run(driver, q.text)
        except Exception as e:
            print(f"    ERROR: {str(e).splitlines()[0]}")
            continue
        print(memgraph.table(cols, rows) if rows else "(no rows)")
    driver.close()


if __name__ == "__main__":
    main()
