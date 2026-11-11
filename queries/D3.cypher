// Task D3 (refactoring): move WatchlistPage's filter logic into a new
// custom hook, useMovieFilter(movies).
// What a model needs to know is described in tasks/D3.md.
// Run with:  uv run python 04_task_context.py D3
// A column named `file` means: put the full source of that file in the context.

// name: D3-1-state-to-move
// WHAT moves: the state the page declares, its setter and initial value.
MATCH (:Function_Component {name: 'WatchlistPage'})-[:DECLARES_STATE]->(s:State_Variable)
RETURN s.name AS state, s.setterName AS setter, s.defaultValue AS initialValue;

// name: D3-2-where-the-filter-flows
// Who receives the filter (and the filtered list) as props. These props must
// keep the same values after the refactoring.
MATCH (:Function_Component {name: 'WatchlistPage'})-[r:PASSES_PROP]->(child)
RETURN child.name AS child, collect(r.propName) AS propsPassed
ORDER BY child;

// name: D3-3-handlers-on-the-page
// Handlers that touch the filter: handleReset sets it back to 'all', so it
// must call the hook's setter afterwards.
MATCH (:Function_Component {name: 'WatchlistPage'})-[:HAS_HANDLER]->(h:EventHandler)
RETURN h.name AS handler, h.eventType AS event;

// name: D3-4-hook-conventions
// How the app's existing custom hooks look: where they live, how they are
// exported, which React hooks they use. The new hook should match.
MATCH (h:Custom_Hook)
OPTIONAL MATCH (h)-[:USES_LIBRARY_HOOK]->(lh:Library_Hook)
OPTIONAL MATCH (h)-[:DECLARES_STATE]->(s:State_Variable)
RETURN h.name AS hook, h.filePath AS filePath, h.exportType AS export,
       collect(DISTINCT lh.name) AS reactHooks, collect(DISTINCT s.name) AS state;

// name: D3-5-callers
// Blast radius: who renders WatchlistPage. A refactoring must not change what
// they see; the page takes no props, so they need no change.
MATCH (caller)-[r:USES_COMPONENT|ROUTES_TO]->(:Function_Component {name: 'WatchlistPage'})
RETURN caller.name AS caller, type(r) AS how, r.path AS route;

// name: D3-6-files-to-read
// The source the model must see: the page, plus one existing hook as a model
// for the new file's style.
MATCH (n)
WHERE (n:Function_Component OR n:Custom_Hook)
  AND n.name IN ['WatchlistPage', 'useMovies']
RETURN n.name AS name, labels(n)[0] AS kind, n.filePath AS file
ORDER BY file;
