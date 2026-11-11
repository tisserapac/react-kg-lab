// Task D2 (feature_addition): add a "Clear watched" button.
// What a model needs to know is described in tasks/D2.md.
// Run with:  uv run python 04_task_context.py D2
// A column named `file` means: put the full source of that file in the context.

// name: D2-1-page-at-route
// WHERE does the button go? The page shown at '/' and its file.
MATCH (router)-[r:ROUTES_TO {path: '/'}]->(page)
RETURN page.name AS page, page.filePath AS filePath, r.path AS route;

// name: D2-2-page-structure
// WHAT is on that page already: its child components, and the handler of the
// existing footer button (handleReset), which the new button can copy.
MATCH (page:Function_Component {name: 'WatchlistPage'})
OPTIONAL MATCH (page)-[:USES_COMPONENT]->(child)
OPTIONAL MATCH (page)-[:HAS_HANDLER]->(h:EventHandler)
RETURN page.name AS page, collect(DISTINCT child.name) AS children,
       collect(DISTINCT h.name + ' (' + h.eventType + ')') AS handlers;

// name: D2-3-data-path
// HOW does the page reach the movie list? Through a custom hook and a Context
// that a Provider fills. The new action has to travel the same path.
MATCH p = (:Function_Component {name: 'WatchlistPage'})-[:USES_CUSTOM_HOOK]->(:Custom_Hook)
          -[:CONSUMES_CONTEXT]->(:Context)<-[:PROVIDES_CONTEXT]-(:Function_Component)
RETURN p;

// name: D2-4-existing-actions
// The pattern to follow: the actions the Provider already shares, and where its
// state comes from. clearWatched joins this list.
MATCH (provider:Function_Component)-[r:PROVIDES_CONTEXT]->(ctx:Context)
OPTIONAL MATCH (provider)-[:DECLARES_STATE]->(s:State_Variable)
OPTIONAL MATCH (provider)-[:USES_CUSTOM_HOOK]->(h:Custom_Hook)
RETURN provider.name AS provider, r.valueExpression AS sharedValue,
       collect(DISTINCT s.name + ' / ' + s.setterName) AS state, collect(DISTINCT h.name) AS stateFrom;

// name: D2-5-other-consumers
// Blast radius: every component that reads the same hook. They will see the
// new action too, and must keep working.
MATCH (c)-[:USES_CUSTOM_HOOK]->(h:Custom_Hook {name: 'useMovies'})
RETURN c.name AS component, c.filePath AS filePath;

// name: D2-6-files-to-read
// The source the model must see to make the change: the page, the Provider,
// and the hook in between.
MATCH (n)
WHERE (n:Function_Component OR n:Custom_Hook)
  AND n.name IN ['WatchlistPage', 'MoviesProvider', 'useMovies']
RETURN n.name AS name, labels(n)[0] AS kind, n.filePath AS file
ORDER BY file;
