# gotcontext.ai VS Code Extension

One-click MCP server configuration for [gotcontext.ai](https://gotcontext.ai) semantic token compression.

## Features

- **Configure MCP Server** — Prompts for your API key and MCP profile, then writes `.vscode/mcp.json` with the gotcontext MCP server entry. Preserves any existing server configurations in the file.
- **Core profile by default** — New configs use `?profile=core`, the lightweight seven-tool compression surface.
- **Full profile option** — Choose Full when your workspace needs the complete MCP catalogue or platform tools such as `gc_pre_flight`.
- **Open Dashboard** — Opens the gotcontext.ai dashboard in your browser to manage API keys, usage, and billing.
- **Status Bar** — Shows a "gotcontext" item in the status bar; click it to run the configure command.

## Getting Started

1. Install the extension.
2. Open a workspace folder in VS Code.
3. Run **gotcontext: Configure MCP Server** from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
4. Enter your API key (starts with `gc_`). Get one at [gotcontext.ai/dashboard](https://gotcontext.ai/dashboard).
5. Choose **Core** for the recommended lightweight setup, or **Full** when you need platform tools such as `gc_pre_flight`.
6. The extension writes `.vscode/mcp.json` — VS Code and compatible MCP clients will pick it up automatically.

## Generated Configuration

The extension writes (or merges into) `.vscode/mcp.json`:

```json
{
  "servers": {
    "gotcontext": {
      "type": "http",
      "url": "https://api.gotcontext.ai/mcp?profile=core",
      "headers": {
        "Authorization": "Bearer gc_live_..."
      }
    }
  }
}
```

## Commands

| Command                            | Description                                     |
| ---------------------------------- | ----------------------------------------------- |
| `gotcontext: Configure MCP Server` | Prompt for API key, write `.vscode/mcp.json`    |
| `gotcontext: Open Dashboard`       | Open https://gotcontext.ai/dashboard in browser |

## Development

```bash
cd sdks/vscode-extension
npm install
npm run compile
```

Press `F5` in VS Code to launch an Extension Development Host for testing.

### Packaging

```bash
npm run package
```

This produces a `.vsix` file you can install locally with `code --install-extension gotcontext-0.2.0.vsix`.

## Requirements

- VS Code 1.85.0 or later
- A gotcontext.ai API key ([get one here](https://gotcontext.ai/dashboard))
