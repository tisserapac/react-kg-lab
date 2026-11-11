# Open questions: where you take it from here

This lab shows the two ends of the approach: an LLM turns source code into structured
data (step 1), and a graph of that data answers the questions a coding task raises
(steps 3 and 4). Everything in between, and much around it, is open. Pick a question,
try something, and bring a proposal.

## Extraction (step 1)

- **When do the examples matter?** On this app, the few-shot and zero-shot runs give the
  same JSON, even with a small model. Find inputs where they differ: `memo` and
  `forwardRef` components, higher-order components, several components per file,
  class components, a component defined inside another. Or remove the JSON shape from
  `system.md` and let the examples alone teach it.
- **Extract more.** Write prompts (and examples) for the other node types of the
  lecture's schema: `Custom_Hook`, `State_Variable`, `EventHandler`, `Context`. One
  prompt per type, or one prompt for everything? What does each cost, and what breaks?
- **Check the extraction.** Compare your JSON with the graph (step 3, query 6). They
  disagree on at least one prop: which, and who is right? How would you measure
  extraction quality on a project you have not read yourself?
- **Prompting vs. parsing.** A parser (Babel, TypeScript's compiler, tree-sitter) finds
  components without an LLM. Which facts can a parser get reliably, and which need
  the LLM's understanding (for example "this handler deletes a movie")?
- **Structured outputs.** Both providers can force the reply to match a JSON schema.
  Does that replace the few-shot examples, or do they still help?

## From JSON to a graph

- **Save your JSON in Memgraph.** Write Cypher (`MERGE`) that turns the output of step 1
  into `Function_Component`, `Prop`, `File` nodes and their relationships, following
  the schema from the lecture. How do you make running it twice safe?
- **Cross-file links.** Step 1 sees one file at a time. `USES_COMPONENT`, `PASSES_PROP`
  and `CONSUMES_CONTEXT` connect files. How would you build them: another LLM call,
  import resolution in Python, or both?
- **Keeping the graph current.** The code changes every day. Which parts of the graph
  must be rebuilt when one file changes?

## Retrieval (steps 3 and 4)

- **Who picks the anchors?** Step 4 starts from components we named by hand
  (`WatchlistPage`, `MoviesProvider`). In the research pipeline an LLM reads the task
  and names them. Try it: what happens when it names something that does not exist yet,
  like `useMovieFilter` in D3?
- **One query per task type.** D2 and D3 have hand-written queries. Can you write *one*
  query for all feature additions and one for all refactorings, taking only the anchor
  names as parameters?
- **How much context is enough?** Leave queries out of `queries/D2.cypher` one at a time.
  Which ones could a model do without? Which missing one makes it fail?
- **What the graph cannot say.** `tasks/D2.md` and `tasks/D3.md` list facts the graph
  does not hold (computed values, what a hook returns, tests, layout). Which would you
  add to the schema, and how would you extract them?

## Evaluation

- **Does the context help?** Give an LLM the task spec with (a) nothing, (b) the whole
  `src/` folder, (c) your context block from step 4, and ask for the change. Apply each
  answer to the app and run the task's test (`../movie-watchlist/tasks/README.md` shows
  how). Which wins, and at what cost in tokens?
- **Beyond this app.** Everything here was tuned on one small app. What would you check
  first on a project with 500 components?
