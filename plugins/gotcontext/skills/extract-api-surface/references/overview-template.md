# Codebase overview reporting format

Reference material for `extract-api-surface`. Use this structure when
returning the skeleton scan to the user.

## Template

```markdown
# <Project name> — API overview

**Scope:** scanned N files, M signatures extracted.
**Compression:** via gotcontext skeleton (~X% smaller than raw).

## Entry points
- `src/main.py` — CLI entry (`main()`)
- `src/server.py` — FastAPI app factory (`create_app()`)

## Modules
### `src/auth/`
One-sentence purpose. Key exports:
- `class AuthMiddleware` — …
- `def verify_jwt(token) -> Claims` — …

### `src/db/`
…

## Type definitions
- `User` (id, email, plan)
- `Subscription` (polar_id, status, current_period_end)

## Notable absences
(things the user might expect but aren't in the surface — public
docs, tests, cli subcommands, etc. — list them)
```

## Good citizens

- Never invent signatures the AST didn't find.
- If skipping a language (regex fallback), flag it.
- Respect `.gitignore` and never include `dist`, `build`,
  `node_modules`, `vendor`, `__pycache__`, etc.
