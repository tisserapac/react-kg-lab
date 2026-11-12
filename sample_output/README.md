# Sample output of step 1 (for students without an API key)

What `01_extract_components.py` produces for the 17 source files of the
movie-watchlist app, so you can follow step 1 without calling an LLM yourself.
Made with the default model, `claude-sonnet-5-5`.

| Path | Command that produces it |
| --- | --- |
| `components/` and `components.json` | `uv run python 01_extract_components.py` (few-shot: with the 3 examples) |
| `components_zero_shot/` and `components_zero_shot.json` | `uv run python 01_extract_components.py --zero-shot` (no examples) |

- `components/src/...`: one JSON file per source file, in the same folders as in the
  app (for example `components/src/components/MovieCard.jsx.json`).
- `components.json`: all 17 results in one list.

Both runs found the same 11 function components, with no errors. Six files have
`"components": []` because they define no component: `main.jsx`, `context/MoviesContext.js`,
`hooks/useLocalStorage.js`, `hooks/useMovies.js` and the two files in `data/`.

Your own runs go to `output/` instead (git-ignored), so they never overwrite these.
