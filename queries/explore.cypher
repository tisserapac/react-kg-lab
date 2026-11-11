// Step 3: Cypher queries to explore the movie-watchlist knowledge graph.
// Run them with:  uv run python 03_explore_graph.py
// or paste one block at a time into Memgraph Lab (http://localhost:3000).
// Queries that RETURN a path (p) are drawn as a graph in Lab.

// name: 1-nodes-by-label
// What kinds of things did the extraction find, and how many of each?
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS nodes
ORDER BY nodes DESC;

// name: 2-relationships-by-type
// And how are they connected?
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS count
ORDER BY count DESC;

// name: 3-component-tree
// The component tree, from the entry file (main.jsx) down to the leaves.
// Route pages count as children of App too (usage: prop_value).
MATCH p = (:File)-[:RENDERS_ROOT_COMPONENT]->(:Function_Component)-[:USES_COMPONENT*0..3]->(leaf)
WHERE NOT (leaf)-[:USES_COMPONENT]->()
RETURN p;

// name: 4-routes
// Which page is shown at which URL?
MATCH (router)-[r:ROUTES_TO]->(page)
RETURN r.path AS path, page.name AS page, page.filePath AS filePath, router.name AS router
ORDER BY path;

// name: 5-props-flow-to-moviecard
// Props are passed down: WatchlistPage -> MovieList -> MovieCard.
// Each PASSES_PROP relationship carries one prop name.
MATCH p = (:Function_Component {name: 'WatchlistPage'})-[r:PASSES_PROP*1..2]->(:Function_Component {name: 'MovieCard'})
WHERE all(x IN r WHERE x.propName = 'onDelete')
RETURN p;

// name: 6-component-interfaces
// Every component's props (its interface), largest first.
MATCH (c:Function_Component)
OPTIONAL MATCH (c)-[:ACCEPTS_PROP]->(p:Prop)
RETURN c.name AS component, count(p) AS props, collect(p.name) AS names
ORDER BY props DESC, component;

// name: 7-state
// Where state lives: state variables, their setters and initial values.
MATCH (owner)-[:DECLARES_STATE]->(s:State_Variable)
RETURN owner.name AS owner, labels(owner)[0] AS kind, s.name AS state, s.setterName AS setter, s.defaultValue AS initialValue
ORDER BY owner, state;

// name: 8-hooks
// Which hooks each component or custom hook calls (React's own, and the app's).
MATCH (c)-[r:USES_LIBRARY_HOOK|USES_CUSTOM_HOOK]->(h)
RETURN c.name AS caller, type(r) AS kind, h.name AS hook
ORDER BY caller, hook;

// name: 9-context-chain
// How pages reach the shared movie list: page -> custom hook -> Context <- Provider.
MATCH p = (page:Function_Component)-[:USES_CUSTOM_HOOK]->(:Custom_Hook)-[:CONSUMES_CONTEXT]->(:Context)<-[:PROVIDES_CONTEXT]-(:Function_Component)
RETURN p;

// name: 10-context-value
// What the Provider puts into the Context: the actions every page can call.
MATCH (provider)-[r:PROVIDES_CONTEXT]->(ctx:Context)
RETURN provider.name AS provider, ctx.name AS context, r.valueExpression AS value;

// name: 11-event-handlers
// Event handlers: which component reacts to which event, with which function.
MATCH (c)-[:HAS_HANDLER]->(e:EventHandler)
RETURN c.name AS component, e.eventType AS event, e.name AS handler
ORDER BY component, event;

// name: 12-who-depends-on-the-context
// Impact analysis: if MoviesContext changes, which components are affected
// (directly, or through a custom hook)?
MATCH (ctx:Context {name: 'MoviesContext'})<-[:CONSUMES_CONTEXT]-(consumer)
OPTIONAL MATCH (user)-[:USES_CUSTOM_HOOK]->(consumer)
RETURN consumer.name AS consumer, labels(consumer)[0] AS kind, collect(user.name) AS usedBy;

// name: 13-libraries
// The npm packages the project depends on (from package.json).
MATCH (:Project)-[d:DEPENDS_ON]->(l:Library)
RETURN l.name AS library, l.category AS category, d.dependencyType AS type
ORDER BY type, category, library;
