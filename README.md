# react-kg-lab

Hands-on lab for the lecture *Knowledge Graphs for React Code Generation*
(Full Stack Application Development, AIT). It works on the
[Movie Watchlist](https://github.com/tisserapac/movie-watchlist) React app in four steps:

1. **Extract** React function components from the app's source with **few-shot
   prompting** of an LLM, and look at the structured JSON it returns.
2. **Import** the app's knowledge graph into **Memgraph**.
3. **Explore** the graph with **Cypher** queries.
4. **Retrieve**: for two coding tasks (D2, D3), find the information each task needs in
   the graph and build a **context block** for an LLM.

The lab shows the idea, not a finished system. The questions it leaves open are in
[docs/ideas.md](docs/ideas.md): that is where your own proposals start.

## Setup

You need **Git**, **Python 3.10+** (installed for you by `uv`), **Docker** (for Memgraph)
and an **API key** for Anthropic or OpenAI. Everything works on Windows, macOS and Linux.

1. **Install uv**, the Python package manager (https://docs.astral.sh/uv/):
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. **Clone both repos into the same folder:**

   ```bash
   git clone https://github.com/tisserapac/movie-watchlist.git
   git clone https://github.com/tisserapac/react-kg-lab.git
   cd react-kg-lab
   uv sync
   ```

   ```
   your-folder/
   ├── movie-watchlist/   the React app, its knowledge graph (knowledge_graph/) and tasks
   └── react-kg-lab/      this repo
   ```

   If `movie-watchlist` is somewhere else, set `APP_DIR` in `.env` or pass `--app <path>`.
3. **Add your API key:** copy `.env.example` to `.env` (`cp .env.example .env`, or in
   PowerShell `Copy-Item .env.example .env`) and fill in `ANTHROPIC_API_KEY`, or set
   `LLM_PROVIDER=openai` and fill in `OPENAI_API_KEY`. `.env` is git-ignored.
4. **Start Memgraph** (from the app's folder, which has the `compose.yaml`):

   ```bash
   cd ../movie-watchlist
   docker compose up -d
   cd ../react-kg-lab
   ```

   Memgraph Lab, the web UI, is then at http://localhost:3000 (click **Connect**).

## Step 1: few-shot extraction

```bash
uv run python 01_extract_components.py --show-prompt --file src/components/MovieCard.jsx
uv run python 01_extract_components.py
```

The first command prints the prompt without calling the LLM. It is a conversation:

- **instructions**: [prompts/function_components/system.md](prompts/function_components/system.md),
  including the JSON shape we want;
- **three examples**, each an example file as the *user* turn and the expected JSON as
  the *assistant* turn: [prompts/function_components/examples/](prompts/function_components/examples/)
  (one has two components, one has none, because it is a custom hook);
- **the real file** as the last user turn.

The second command sends every `.js`/`.jsx` file of the app (17 files, about 10 s),
checks each reply against the schema (`pydantic`), prints the JSON and saves it in
`output/components/`. Expected result: 11 function components.

Try `--zero-shot` (no examples) and compare. On this small app the result is the
same; finding where examples *do* matter is the first question in
[docs/ideas.md](docs/ideas.md). To add an example, add a `NN_name.jsx` + `NN_name.json` pair.

Storing this JSON as nodes and relationships with Cypher is left to you (see the ideas).
The graph you import in step 2 was built that way by the full research pipeline, from
more prompts (props, hooks, state, context, routes, ...) than this one.

## Step 2: import a graph

```bash
uv run python 02_import_graph.py movie-watchlist   # the full app: 81 nodes, 118 relationships
uv run python 02_import_graph.py lab-solution      # the small lab version: 51 nodes, 71 relationships
```

The graphs are in `../movie-watchlist/knowledge_graph/` as CYPHERL: one Cypher statement
per line. The script deletes everything in Memgraph first (it asks), so **one graph at a
time**. Import `lab-solution`, look at it, then import `movie-watchlist`: what did the
custom hooks, the Context and the router add?

## Step 3: explore with Cypher

```bash
uv run python 03_explore_graph.py --list   # the 13 queries
uv run python 03_explore_graph.py          # run them all
uv run python 03_explore_graph.py 3 9      # only queries 3 and 9
```

The queries are in [queries/explore.cypher](queries/explore.cypher), each with a comment
saying what it asks. Paste them into Memgraph Lab too: queries that return a path, such
as 3 (the component tree), 5 (how a prop travels down) and 9 (page → hook → Context ←
Provider), are drawn as a graph there. Write your own in a new `.cypher` file and run it
with `--file`.

## Step 4: context for a coding task

Two tasks on the app (in `../movie-watchlist/tasks/`):

- **D2**, a feature: add a "Clear watched" button. See [tasks/D2.md](tasks/D2.md).
- **D3**, a refactoring: move the filter logic into a `useMovieFilter` hook. See [tasks/D3.md](tasks/D3.md).

Each `tasks/D*.md` explains what information the task needs and why, and what the graph
cannot tell you. The matching queries are in `queries/D2.cypher` and `queries/D3.cypher`.

```bash
uv run python 02_import_graph.py movie-watchlist   # if it is not loaded
uv run python 04_task_context.py D2 --print
uv run python 04_task_context.py D3
```

The script runs the task's queries and writes `output/D2_context.md`: the spec, what each
query found, and the full source of the files the queries point to. That block is what
an LLM would get instead of the whole project. Compare it with the research pipeline's
block for the same task in `../movie-watchlist/tasks/contexts/`.

## Costs and models

Step 1 makes one LLM call per file (17 calls). The default model is `claude-opus-5-5`
(Anthropic) or `gpt-5.5` (OpenAI); set `LLM_MODEL` in `.env` to use another, for example a
smaller, cheaper one. Steps 2–4 make no LLM calls.

## Files

```
01_extract_components.py   step 1
02_import_graph.py         step 2
03_explore_graph.py        step 3
04_task_context.py         step 4
kglab/                     shared code: settings, LLM call, Memgraph helpers
prompts/function_components/   the few-shot prompt: instructions + examples
queries/                   Cypher: explore.cypher, D2.cypher, D3.cypher
tasks/                     what D2 and D3 need from the graph
docs/ideas.md              open questions for your proposals
output/                    what the scripts write (git-ignored)
```
