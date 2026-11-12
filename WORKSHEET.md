# Worksheet: knowledge graphs for React code generation

This worksheet walks you through the live demo of the lecture at your own pace. It
takes about an hour. Every step says what to type and what you should see. Questions
to think about are marked **Q**; click *Answer* to check yourself.

You work in two folders that sit next to each other: `movie-watchlist` (the React app)
and `react-kg-lab` (this repo). Commands starting with `uv run` are typed in
`react-kg-lab`.

---

## Part 0: Get ready (5 min)

1. If you have not set up yet, follow **Setup** in [README.md](README.md) first.
2. Start Memgraph (the graph database). In the `movie-watchlist` folder:

   ```bash
   docker compose up -d
   ```

3. Open http://localhost:3000 in your browser and click **Connect**. This is
   **Memgraph Lab**, where you can type Cypher queries and see the graph.
4. Go to the `react-kg-lab` folder for the rest of the worksheet:

   ```bash
   cd ../react-kg-lab
   ```

> **No API key?** You can still do everything. In Part 1, do steps 1–2 and read the
> example output given there; Parts 2–5 need no key.

---

## Part 1: Extract structured data with an LLM (15 min)

The idea: we show the LLM a few **examples** of "code in → JSON out", then give it a
new file. It answers in the same JSON shape. This is called **few-shot prompting**.

**Step 1. Look at the prompt** (no LLM call, free):

```bash
uv run python 01_extract_components.py --show-prompt --file src/components/MovieCard.jsx
```

You should see:

- `=== SYSTEM ===`: the instructions, including the JSON shape we want;
- three `=== USER ===` / `=== ASSISTANT ===` pairs: the **examples**;
- a last `=== USER ===` with `MovieCard.jsx`, the file we want analysed.

**Step 2. Look at the examples as files.** Open the folder
`prompts/function_components/examples/`. Each example is a pair: a `.jsx` (or `.js`)
file and the `.json` answer we expect for it.

**Q1.** Example 3 (`03_use_window_width.js`) expects `{"components": []}`. Why include
an example with an *empty* answer?

<details><summary>Answer</summary>

It teaches the model what **not** to report. `useWindowWidth` is a custom hook: it is a
function, but it returns a number, not JSX, so it is not a component. Without such an
example, a model might list every function it sees.

**Optional: compare with a syntax tree (5 min).** A parser reads code into an
*abstract syntax tree* (AST). Let's see what it says about the same file.

1. Open https://astexplorer.net/ (the language at the top should be **JavaScript**).
2. Copy the whole of `prompts/function_components/examples/03_use_window_width.js`
   and paste it into the left box, replacing what is there.
3. The right box shows the AST. Switch it to **JSON** to see it as text. Shortened,
   it looks like this:

   ```json
   {
     "type": "Program",
     "body": [
       { "type": "ImportDeclaration", "source": { "value": "react" } },
       {
         "type": "FunctionDeclaration",
         "id": { "type": "Identifier", "name": "useWindowWidth" },
         "params": [],
         "body": { "type": "BlockStatement", "body": [
           { "type": "VariableDeclaration" },
           { "type": "ExpressionStatement" },
           { "type": "ReturnStatement", "argument": { "type": "Identifier", "name": "width" } }
         ] }
       },
       { "type": "ExportDefaultDeclaration", "declaration": { "type": "Identifier", "name": "useWindowWidth" } }
     ]
   }
   ```

The AST describes **syntax**: `useWindowWidth` is a `FunctionDeclaration` that returns
an identifier. A component such as `function Greeting(...)` in example 1 is *also* a
`FunctionDeclaration`. Nothing in the tree says "custom hook" or "component"; to tell
them apart from an AST you would write the rules yourself (does the name start with
`use`? does it return JSX?). The few-shot prompt gives the LLM those ideas through the
instructions and examples, and it answers in terms of React concepts: `{"components": []}`.

**Q1b.** What does the parser do better than the LLM? (Think: cost, speed, and whether
the answer is ever wrong.) This trade-off is one of the open questions in
[docs/ideas.md](docs/ideas.md) ("Prompting vs. parsing").
</details>

**Step 3. Run it on one file** (needs an API key in `.env`):

```bash
uv run python 01_extract_components.py --file src/components/MovieCard.jsx
```

You should see this JSON (after about 5 seconds):

```json
{
  "components": [
    {
      "name": "MovieCard",
      "syntax": "function",
      "exportType": "default",
      "props": ["title", "year", "genre", "watched", "onToggle", "onDelete"],
      "hooks": []
    }
  ]
}
```

Open `../movie-watchlist/src/components/MovieCard.jsx` and check that every value is right.

**Step 4. Run it on the whole app:**

```bash
uv run python 01_extract_components.py
```

It reads 17 files (about 10 seconds) and ends with a list:
`Found 11 function components in 17 files (0 errors)`. The JSON for each file is saved
in `output/components/`.

**Q2.** Six files gave `{"components": []}`, for example `src/hooks/useMovies.js` and
`src/main.jsx`. Is that correct?

<details><summary>Answer</summary>

Yes. `useMovies.js` and `useLocalStorage.js` define custom hooks, `MoviesContext.js`
creates a Context, `data/*.js` hold data, and `main.jsx` only *renders* `<App />`; it
does not define a component.
</details>

**Step 5. Try it without the examples:**

```bash
uv run python 01_extract_components.py --zero-shot
```

**Q3.** Is the result different? What does that tell you?

<details><summary>Answer</summary>

On this app the result is the same. The app's code is clean and the instructions
already describe the JSON shape, so a strong model does not need examples here.
Examples start to matter on harder code (for example `memo`, `forwardRef`, several
components in one file) or with smaller models. Finding out *where* is one of the open
questions in [docs/ideas.md](docs/ideas.md).
</details>

---

## Part 2: Load the knowledge graph (5 min)

The research pipeline has already turned the whole app into a knowledge graph and saved
it as a text file of Cypher statements (`../movie-watchlist/knowledge_graph/`). We load
it into Memgraph. Only one graph is loaded at a time.

**Step 1. Load the small graph** (the simple lab version of the app):

```bash
uv run python 02_import_graph.py lab-solution
```

If it asks `Delete them all? [y/N]`, type `y`. It ends with
`Graph loaded: 51 nodes, 71 relationships.`

In Memgraph Lab, type this query and run it:

```cypher
MATCH (n)-[r]->(m) RETURN n, r, m;
```

You see the whole small graph: circles are **nodes** (components, files, props, ...),
lines are **relationships**. Click a node to see its properties.

**Step 2. Load the full graph:**

```bash
uv run python 02_import_graph.py movie-watchlist
```

It ends with `Graph loaded: 81 nodes, 118 relationships.` Run `MATCH (n)-[r]->(m) RETURN n, r, m;` in
Lab again.

**Q4.** The full app has 30 more nodes. Compare the two tables the script printed:
which kinds of nodes and relationships are new?

<details><summary>Answer</summary>

The full app adds `Custom_Hook` (2: `useLocalStorage`, `useMovies`), `Context` (1:
`MoviesContext`) and routes (`ROUTES_TO`, 3: `/`, `/stats`, `*`), and the relationships
between them (`USES_CUSTOM_HOOK`, `PROVIDES_CONTEXT`, `CONSUMES_CONTEXT`). These are the
React ideas from the lecture: custom hooks, Context and routing.
</details>

---

## Part 3: Ask the graph questions with Cypher (15 min)

**Step 1. Run the prepared queries:**

```bash
uv run python 03_explore_graph.py --list
uv run python 03_explore_graph.py 3 9
```

Query 3 prints the component tree; query 9 shows how the pages reach the movie list:
`WatchlistPage → useMovies → MoviesContext ← MoviesProvider`.

**Step 2. See them as a graph.** Open [queries/explore.cypher](queries/explore.cypher),
copy the block of query `9-context-chain` (from `MATCH` to `;`), paste it into Memgraph
Lab and run it. Queries that return a path (`RETURN p`) are drawn as a graph.

**Step 3. Read a query.** This one is from the lecture slides:

```cypher
MATCH (h)-[:CONSUMES_CONTEXT]->(c:Context)
RETURN h.name, c.name;
```

Read it as: *find any node `h` with a `CONSUMES_CONTEXT` arrow to a node `c` labelled
`Context`; show their names.* Run it in Lab. Result: `useMovies`, `MoviesContext`.

**Step 4. Write your own.** Try these in Lab before opening the answers. Start from
the query in Step 3 and change the arrow type and the names.

**Q5.** Which components does `WatchlistPage` render? (Arrow type: `USES_COMPONENT`.)

<details><summary>Answer</summary>

```cypher
MATCH (:Function_Component {name: 'WatchlistPage'})-[:USES_COMPONENT]->(c)
RETURN c.name;
```

`AddMovieForm`, `FilterBar`, `MovieList`.
</details>

**Q6.** Which props does `MovieCard` receive, and from whom? (Arrow type: `PASSES_PROP`;
the prop's name is stored on the arrow as `propName`.)

<details><summary>Answer</summary>

```cypher
MATCH (parent)-[r:PASSES_PROP]->(:Function_Component {name: 'MovieCard'})
RETURN parent.name AS parent, collect(r.propName) AS props;
```

`MovieList` passes `title, year, genre, watched, onToggle, onDelete`. `collect(...)`
gathers many rows into one list.
</details>

**Q7.** Where does state live? List each owner with its state variables. (Arrow type:
`DECLARES_STATE`.)

<details><summary>Answer</summary>

```cypher
MATCH (owner)-[:DECLARES_STATE]->(s)
RETURN owner.name AS owner, collect(s.name) AS state
ORDER BY owner;
```

`AddMovieForm`: title, year, genre, error · `MoviesProvider`: movies ·
`WatchlistPage`: filter · `useLocalStorage`: value.

**Tip:** after `collect(...)`, sort by the name you gave in `RETURN` (`ORDER BY owner`),
not by `owner.name`; Memgraph reports "Unbound variable" otherwise.
</details>

**Q8.** In Part 1 the LLM said `MoviesProvider` has a prop called `children`. Does the
graph agree? (Run query 6: `uv run python 03_explore_graph.py 6`.)

<details><summary>Answer</summary>

No: in the graph `MoviesProvider` has 0 props. The graph was built by a different
pipeline with different prompts. Neither is "the truth" until you check the code
(`MoviesProvider({ children })` does receive `children`). How would you measure which
extraction is better on a project too big to check by hand?
</details>

---

## Part 4: Build the context for a coding task (15 min)

An LLM writes better code when it gets the **right** parts of the project, not all of
it. Here the graph picks those parts for two tasks on the app:

- **D2**: add a "Clear watched" button (a new feature);
- **D3**: move the filter logic into a new `useMovieFilter` hook (a refactoring).

**Step 1. Read [tasks/D2.md](tasks/D2.md).** Its table lists the questions you would ask
before adding the button, and the query that answers each one.

**Step 2. Build the context block:**

```bash
uv run python 04_task_context.py D2
```

It runs the six queries in [queries/D2.cypher](queries/D2.cypher) and writes
`output/D2_context.md` (about 1,400 tokens). Open that file: the task, what each query
found, and the source of three files (`WatchlistPage`, `MoviesProvider`, `useMovies`).
This block is what you would give an LLM together with the task.

> If it says *"The graph in Memgraph has no custom hooks"*, you still have the small
> graph loaded: run `uv run python 02_import_graph.py movie-watchlist`.

**Q9.** The button goes in `WatchlistPage.jsx`, and `clearWatched` goes in
`MoviesProvider.jsx`. Neither file mentions the other. How did the graph know that both
are needed?

<details><summary>Answer</summary>

Query `D2-3-data-path` follows the arrows `WatchlistPage → useMovies → MoviesContext ←
MoviesProvider`. The connection only exists through the hook and the Context. Searching
the text of `WatchlistPage.jsx` for "MoviesProvider" would find nothing.
</details>

**Step 3. Compare** `output/D2_context.md` with the research pipeline's block for the
same task: `../movie-watchlist/tasks/contexts/D2_kg_augmented_context.md`. What does
each include that the other does not?

**Step 4. Now D3 on your own.** Read [tasks/D3.md](tasks/D3.md), then:

```bash
uv run python 04_task_context.py D3
```

**Q10.** The research pipeline's LLM read the D3 task and named `useMovieFilter` as one
of the components to look up. The graph found nothing for it. Why?

<details><summary>Answer</summary>

`useMovieFilter` does not exist yet: the task asks you to create it. A graph only holds
what is already in the code. Retrieval has to cope with names that come from the task,
not from the project.
</details>

**Q11.** `tasks/D2.md` and `tasks/D3.md` each end with "What the graph does not tell you".
Pick one item. Could you add it to the graph? What would you extract, and how?

---

## Part 5: Your proposal (5 min)

Open [docs/ideas.md](docs/ideas.md). It lists open questions about extraction, about
turning the JSON into a graph, about retrieval and about evaluation. Pick one that
interests you and write a short proposal: what you would try, and how you would know
whether it worked.

---

## When you are done

Stop Memgraph (your data is kept) in the `movie-watchlist` folder:

```bash
docker compose down
```

## If something goes wrong

| Message | What to do |
| --- | --- |
| `Cannot reach Memgraph at bolt://localhost:7687` | Start Docker Desktop, then `docker compose up -d` in `movie-watchlist`. |
| `No ANTHROPIC_API_KEY set` | Put your key in `.env`, or skip steps 3–5 of Part 1. |
| `Cannot find the movie-watchlist app` | Both folders must be next to each other (see README, Setup). |
| `The graph in Memgraph has no custom hooks` | `uv run python 02_import_graph.py movie-watchlist` |
| Memgraph Lab shows nothing | Click **Connect** first; then run `MATCH (n)-[r]->(m) RETURN n, r, m;`. |
| `Unbound variable` in a query | After `collect(...)`, `ORDER BY` the name you gave in `RETURN`. |
