# Change Log

All notable changes to the **gotcontext.ai** VS Code extension are documented here.

## [0.2.0] — 2026-05-21

### Added

- Added MCP profile selection during configuration.
- New workspace configs default to `https://api.gotcontext.ai/mcp?profile=core`.
- Added a Full profile option for users who need the complete MCP catalogue or platform tools such as `gc_pre_flight`.
- Generated `.vscode/mcp.json` entries now include `"type": "http"`.

## [0.1.2] — 2026-04-19

### Changed

- Metadata bump in sync with gotcontext API v1.4.1. No extension
  behaviour changes — the v1.4.0 surfaces (output-style appendix,
  sensitive-content refuse, `X-Fidelity-Warning`, per-tenant
  semantic-cache threshold, `by_source` breakdown) are exposed via
  the TypeScript SDK and the dashboard today; a dedicated extension
  release will surface them in-editor in a later sprint.

## [0.1.0] — 2026-04-15

### Added

- **Configure MCP Server** command (`gotcontext: Configure MCP Server`): prompts for
  your `gc_` API key and writes `.vscode/mcp.json` so VS Code, Cursor, and compatible
  editors automatically load the gotcontext MCP server.
- **Open Dashboard** command (`gotcontext: Open Dashboard`): opens
  `https://gotcontext.ai/dashboard` in your default browser.
- Status-bar item (bottom-right): one-click shortcut to the Configure command.
- Supports multi-root workspaces — writes config into the first workspace folder.
- Validates API key format (must start with `gc_`) before writing.
- Gracefully merges into an existing `.vscode/mcp.json` without clobbering other
  server entries.
