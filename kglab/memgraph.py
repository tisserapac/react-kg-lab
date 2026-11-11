"""Connecting to Memgraph, reading .cypher files, and printing query results."""
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from neo4j.graph import Node, Path as GraphPath, Relationship

from kglab import settings


def connect():
    """A driver for Memgraph (the neo4j driver speaks Memgraph's Bolt protocol)."""
    driver = GraphDatabase.driver(settings.MEMGRAPH_URI, auth=("", ""))
    try:
        driver.verify_connectivity()
    except ServiceUnavailable:
        sys.exit(
            f"Cannot reach Memgraph at {settings.MEMGRAPH_URI}.\n"
            "Start it in the movie-watchlist folder with:  docker compose up -d"
        )
    return driver


def run(driver, query: str, params: dict | None = None) -> tuple[list[str], list[list]]:
    """Run one query; return (column names, rows)."""
    with driver.session() as session:
        result = session.run(query, params or {})
        rows = [list(record.values()) for record in result]
        return list(result.keys()), rows


# ── .cypher files ────────────────────────────────────────────────────────────

@dataclass
class NamedQuery:
    name: str
    why: str
    text: str


def load_queries(path: Path) -> list[NamedQuery]:
    """Split a .cypher file into queries.

    Each query starts with a `// name: ...` line, optionally followed by
    `// ...` comment lines that explain it. The whole block can also be pasted
    into Memgraph Lab as is.
    """
    queries: list[NamedQuery] = []
    blocks = re.split(r"^(?=// name:)", path.read_text(encoding="utf-8"), flags=re.M)
    for block in blocks:
        if not block.startswith("// name:"):
            continue
        lines = block.strip().splitlines()
        name = lines[0].removeprefix("// name:").strip()
        why = []
        i = 1
        while i < len(lines) and lines[i].startswith("//"):
            why.append(lines[i].removeprefix("//").strip())
            i += 1
        text = "\n".join(lines[i:]).strip().rstrip(";")
        queries.append(NamedQuery(name, " ".join(w for w in why if w), text))
    return queries


# ── printing results ────────────────────────────────────────────────────────

def show(value) -> str:
    """A short, readable form of a value: nodes by name, paths as arrows."""
    if isinstance(value, GraphPath):
        nodes, rels = value.nodes, value.relationships
        out = show(nodes[0])
        for here, rel, nxt in zip(nodes, rels, nodes[1:]):
            forward = rel.start_node.element_id == here.element_id
            out += f" -[{rel.type}]-> " if forward else f" <-[{rel.type}]- "
            out += show(nxt)
        return out
    if isinstance(value, Node):
        label = next(iter(value.labels), "")
        name = value.get("name") or value.get("filePath") or value.get("projectId") or ""
        return f"({name}:{label})"
    if isinstance(value, Relationship):
        return f"[{value.type}]"
    if isinstance(value, list):
        return ", ".join(show(v) for v in value)
    if value is None:
        return ""
    return str(value)


def table(columns: list[str], rows: list[list], markdown: bool = False) -> str:
    """Format rows as a plain-text table (or a Markdown table)."""
    cells = [[show(v) for v in row] for row in rows]
    if markdown:
        lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
        lines += ["| " + " | ".join(c.replace("|", "\\|") for c in row) + " |" for row in cells]
        return "\n".join(lines)
    if len(columns) == 1:  # e.g. paths: print them in full
        return "\n".join([columns[0], "-" * len(columns[0])] + [row[0] for row in cells])
    limit = 70
    widths = [len(c) for c in columns]
    for row in cells:
        widths = [min(max(w, len(c)), limit) for w, c in zip(widths, row)]
    def fmt(row):
        return "  ".join((c if len(c) <= limit else c[:limit - 3] + "...").ljust(w) for c, w in zip(row, widths))
    return "\n".join([fmt(columns), fmt(["-" * w for w in widths])] + [fmt(r) for r in cells])
