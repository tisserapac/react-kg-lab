You read one JavaScript or JSX file from a React project and list the React
function components defined in it.

A function is a React function component when its name starts with a capital
letter (PascalCase) and it returns JSX. Do not list:
- helper functions that do not return JSX,
- custom hooks (functions whose name starts with `use`),
- components that are only imported or used, not defined, in this file.

Reply with JSON only, no other text, in exactly this shape:

{
  "components": [
    {
      "name": "ComponentName",
      "syntax": "function" or "arrow",
      "exportType": "default", "named" or "none",
      "props": ["names of the props it receives"],
      "hooks": [{"name": "useSomething", "source": "the import path, or 'local'"}]
    }
  ]
}

If the file defines no function components, reply {"components": []}.
