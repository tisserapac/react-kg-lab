# Context for task D2 (feature_addition)

## Task

The watchlist has no way to remove all watched movies at once. Add a `clearWatched` action to `MoviesProvider` that removes every watched movie and keeps the rest, and make it available through the `useMovies` hook. Then add a "Clear watched" button to the footer of `WatchlistPage` that calls it. The button should be disabled when no movie is watched.

## What the knowledge graph says

### D2-1-page-at-route

_WHERE does the button go? The page shown at '/' and its file._

| page | filePath | route |
|---|---|---|
| WatchlistPage | src/pages/WatchlistPage.jsx | / |

### D2-2-page-structure

_WHAT is on that page already: its child components, and the handler of the existing footer button (handleReset), which the new button can copy._

| page | children | handlers |
|---|---|---|
| WatchlistPage | AddMovieForm, FilterBar, MovieList | handleReset (onClick) |

### D2-3-data-path

_HOW does the page reach the movie list? Through a custom hook and a Context that a Provider fills. The new action has to travel the same path._

| p |
|---|
| (WatchlistPage:Function_Component) -[USES_CUSTOM_HOOK]-> (useMovies:Custom_Hook) -[CONSUMES_CONTEXT]-> (MoviesContext:Context) <-[PROVIDES_CONTEXT]- (MoviesProvider:Function_Component) |

### D2-4-existing-actions

_The pattern to follow: the actions the Provider already shares, and where its state comes from. clearWatched joins this list._

| provider | sharedValue | state | stateFrom |
|---|---|---|---|
| MoviesProvider | { movies, addMovie, toggleMovie, deleteMovie, resetMovies } | movies / setMovies | useLocalStorage |

### D2-5-other-consumers

_Blast radius: every component that reads the same hook. They will see the new action too, and must keep working._

| component | filePath |
|---|---|
| StatsPage | src/pages/StatsPage.jsx |
| WatchlistPage | src/pages/WatchlistPage.jsx |

### D2-6-files-to-read

_The source the model must see to make the change: the page, the Provider, and the hook in between._

| name | kind | file |
|---|---|---|
| MoviesProvider | Function_Component | src/context/MoviesProvider.jsx |
| useMovies | Custom_Hook | src/hooks/useMovies.js |
| WatchlistPage | Function_Component | src/pages/WatchlistPage.jsx |

## Source files

### `src/context/MoviesProvider.jsx`

```jsx
import MoviesContext from './MoviesContext';
import initialMovies from '../data/initialMovies';
import useLocalStorage from '../hooks/useLocalStorage';

// A key unique to this app, so another app on localhost:5173
// (for example your own lab version) cannot overwrite our list.
const STORAGE_KEY = 'movie-watchlist:movies';

function MoviesProvider({ children }) {
  // the sample movies are used only when nothing has been saved yet
  const [movies, setMovies] = useLocalStorage(STORAGE_KEY, initialMovies);

  function addMovie(newMovie) {
    setMovies([...movies, newMovie]);
  }

  function toggleMovie(id) {
    setMovies(movies.map((m) =>
      m.id === id ? { ...m, watched: !m.watched } : m
    ));
  }

  function deleteMovie(id) {
    setMovies(movies.filter((m) => m.id !== id));
  }

  function resetMovies() {
    setMovies(initialMovies);
  }

  return (
    <MoviesContext.Provider value={{ movies, addMovie, toggleMovie, deleteMovie, resetMovies }}>
      {children}
    </MoviesContext.Provider>
  );
}

export default MoviesProvider;
```

### `src/hooks/useMovies.js`

```js
import { useContext } from 'react';
import MoviesContext from '../context/MoviesContext';

// The one way components reach the movie list: reads MoviesContext and adds
// values calculated from it, so no component has to recalculate them.
function useMovies() {
  const context = useContext(MoviesContext);
  if (context === null) {
    throw new Error('useMovies must be used inside <MoviesProvider>.');
  }

  const watchedCount = context.movies.filter((m) => m.watched).length;

  return { ...context, watchedCount };
}

export default useMovies;
```

### `src/pages/WatchlistPage.jsx`

```jsx
import { useState } from 'react';
import AddMovieForm from '../components/AddMovieForm';
import FilterBar from '../components/FilterBar';
import MovieList from '../components/MovieList';
import useMovies from '../hooks/useMovies';
import './WatchlistPage.css';

function WatchlistPage() {
  const { movies, watchedCount, addMovie, toggleMovie, deleteMovie, resetMovies } = useMovies();
  const [filter, setFilter] = useState('all');

  function handleReset() {
    resetMovies();
    setFilter('all');
  }

  // calculated, NOT stored in state
  const visibleMovies = movies.filter(
    (m) => filter === 'all' || (filter === 'watched') === m.watched
  );

  const emptyMessage = movies.length === 0
    ? 'Your watchlist is empty. Add a movie above.'
    : 'No movies match this filter.';

  return (
    <>
      <AddMovieForm onAdd={addMovie} />

      <div className="watchlist__toolbar">
        <p className="watchlist__summary">
          Total: {movies.length} · Watched: {watchedCount} / {movies.length}
        </p>
        <FilterBar filter={filter} onFilterChange={setFilter} />
      </div>

      <MovieList
        movies={visibleMovies}
        emptyMessage={emptyMessage}
        onToggle={toggleMovie}
        onDelete={deleteMovie}
      />

      <div className="watchlist__footer">
        <button type="button" className="watchlist__reset" onClick={handleReset}>
          Reset to sample movies
        </button>
      </div>
    </>
  );
}

export default WatchlistPage;
```
