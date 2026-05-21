# VS Code Extension SDK Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the public `gotcontext-sdk` install surfaces into parity with the current gotcontext.ai MCP behavior, including the VS Code extension surface that is currently absent from this repo.

**Architecture:** Treat `C:/dev/projects/gotcontext-main` as the source of truth for public SDK/plugin artifacts, but do not copy private API/dashboard internals. Port the tracked public files needed for MCP installation, then patch the VS Code extension to default new installs to the lightweight `?profile=core` MCP surface while allowing users to choose `full` when they need platform tools such as `gc_pre_flight`. The server default remains unchanged: bare `/mcp` still resolves to `full`; this plan only changes new client install defaults.

**Tech Stack:** VS Code extension TypeScript, Node/npm/vsce, Claude Code plugin JSON/skills/hooks, GitHub Actions.

---

### Task 1: Verify Current Drift

**Files:**
- Read: `C:/dev/projects/gotcontext-sdk/plugins/gotcontext/mcp-servers/gotcontext.json`
- Read: `C:/dev/projects/gotcontext-main/plugins/gotcontext/mcp-servers/gotcontext.json`
- Read: `C:/dev/projects/gotcontext-main/api/app/mcp_gateway.py`
- Read: `C:/dev/projects/gotcontext-main/token-saver-5000/tests/test_tool_profiles.py`
- Read: `C:/dev/projects/gotcontext-main/sdks/vscode-extension/src/extension.ts`

- [x] **Step 1: Confirm SDK repo lacks the extension**

Run: `Test-Path sdks/vscode-extension`

Expected: `False`.

- [x] **Step 2: Confirm main MCP profile behavior**

Evidence: `api/app/mcp_gateway.py` documents `profile=core` / `profile=full` routing and defaults missing/invalid `profile` to `full`.

- [x] **Step 3: Confirm core profile tool contract**

Evidence: `token-saver-5000/tests/test_tool_profiles.py` pins the 7 core tools: `ingest_context`, `read_skeleton`, `search_semantic`, `modulate_region`, `get_stats`, `list_documents`, `delete_document`.

### Task 2: Port Public MCP Install Surfaces

**Files:**
- Modify: `plugins/gotcontext/.claude-plugin/plugin.json`
- Modify: `plugins/gotcontext/mcp-servers/gotcontext.json`
- Create: `plugins/gotcontext/.claude-plugin/hooks/hooks.json`
- Create: `plugins/gotcontext/.claude-plugin/hooks/gotcontext-sessionstart.sh`
- Create: `plugins/gotcontext/.claude-plugin/hooks/gotcontext-precompact.sh`
- Create: `plugins/gotcontext/.claude-plugin/hooks/gotcontext-stop.sh`
- Create: `plugins/gotcontext/skills/pre-flight/SKILL.md`
- Create: `plugins/gotcontext/skills/session-summary/SKILL.md`
- Create: `plugins/gotcontext/skills/compress-mcp-manifest/SKILL.md`
- Modify: `plugins/gotcontext/skills/review-pr-diff/SKILL.md`
- Modify: `README.md`

- [x] **Step 1: Copy tracked plugin updates from main**

Copy only files tracked by `git ls-files` in `C:/dev/projects/gotcontext-main/plugins/gotcontext`; do not copy local secrets, generated files, caches, or untracked files.

- [x] **Step 2: Verify plugin MCP default is core**

Run: `Get-Content -Raw plugins/gotcontext/mcp-servers/gotcontext.json`

Expected: URL is `https://api.gotcontext.ai/mcp?profile=core` and comment explains how to switch to `?profile=full`.

- [x] **Step 3: Update root README quickstart**

Change the MCP quickstart URL to `https://api.gotcontext.ai/mcp?profile=core`, explain that `core` exposes the 7 lightweight compression tools, and mention `?profile=full` for the full catalogue and platform tools such as `gc_pre_flight`. Do not add unverified public numeric claims such as exact full-profile tool counts or token cost for `tools/list`.

### Task 3: Add and Patch the VS Code Extension

**Files:**
- Create: `sdks/vscode-extension/.vscodeignore`
- Create: `sdks/vscode-extension/CHANGELOG.md`
- Create: `sdks/vscode-extension/README.md`
- Create: `sdks/vscode-extension/images/icon.png`
- Create: `sdks/vscode-extension/package-lock.json`
- Create: `sdks/vscode-extension/package.json`
- Create: `sdks/vscode-extension/eslint.config.mjs`
- Create: `sdks/vscode-extension/src/extension.ts`
- Create: `sdks/vscode-extension/src/extension.test.ts`
- Create: `sdks/vscode-extension/tsconfig.json`

- [x] **Step 1: Port the tracked extension from main**

Copy only `git ls-files sdks/vscode-extension` from `C:/dev/projects/gotcontext-main`. Add `vitest` to `devDependencies` and add a `test` script because the extension tests below use Vitest and main's extension package currently has no test runner. Add local ESLint dependencies/config because the ported package has a `lint` script but no local `eslint` dependency or config.

- [x] **Step 2: Write the failing tests**

Add `sdks/vscode-extension/src/extension.test.ts` with tests for:

```ts
import { describe, expect, it } from "vitest";
import { buildMcpServerConfig, mcpServerUrlForProfile } from "./extension";

describe("MCP profile URLs", () => {
  it("defaults new installs to the lightweight core profile", () => {
    expect(mcpServerUrlForProfile("core")).toBe("https://api.gotcontext.ai/mcp?profile=core");
  });

  it("supports the full profile for platform tools", () => {
    expect(mcpServerUrlForProfile("full")).toBe("https://api.gotcontext.ai/mcp?profile=full");
  });

  it("writes the selected profile URL and bearer header", () => {
    expect(buildMcpServerConfig("gc_live_test", "core")).toEqual({
      type: "http",
      url: "https://api.gotcontext.ai/mcp?profile=core",
      headers: { Authorization: "Bearer gc_live_test" },
    });
  });
});
```

Expected before implementation: test runner fails because these exported helpers do not exist.

- [x] **Step 3: Implement minimal extension helpers**

Export `mcpServerUrlForProfile(profile)` and `buildMcpServerConfig(apiKey, profile)`. Preserve the existing command behavior, but use `vscode.window.showQuickPick` to prompt for `Core (recommended)` or `Full` before writing `.vscode/mcp.json`, defaulting to `Core`. Add `type: "http"` to the `McpServerConfig` interface and to the generated server config.

- [x] **Step 4: Update extension metadata and docs**

Set extension version to `0.2.0`, update package repository/bugs URLs to `gotcontext-sdk`, add `"test": "vitest run"`, add local ESLint dependencies/config, and update README/CHANGELOG with core/full profile behavior and the `gc_pre_flight` caveat.

### Task 4: Add Release Automation

**Files:**
- Create: `.github/workflows/publish-vscode-extension.yml`
- Create: `.github/workflows/check-extension-drift.yml`

- [x] **Step 1: Port extension publish workflow**

Copy the publish workflow from main and update GitHub links from `gotcontext-main` to `gotcontext-sdk`. Document that the SDK repo must configure `VSCE_PAT` in GitHub Actions secrets before marketplace publishing can succeed.

- [x] **Step 2: Make drift workflow useful in this public SDK repo**

Because this repo does not contain `api/app/mcp_gateway.py` or `token-saver-5000`, do not ship a fake API drift gate. Instead, make the workflow validate extension/plugin install defaults on PRs that touch MCP install surfaces.

### Task 5: Validate, Commit, Push, and Merge

**Files:**
- Verify: all changed files

- [x] **Step 1: Run extension tests**

Run: `npm test` in `sdks/vscode-extension`

Expected: PASS.

- [x] **Step 2: Run extension compile/lint/package**

Run: `npm run compile`, `npm run lint`, and `npm run package` in `sdks/vscode-extension`

Expected: PASS and `.vsix` build succeeds.

- [x] **Step 3: Run plugin JSON validation**

Run: `Get-Content plugins/gotcontext/mcp-servers/gotcontext.json -Raw | ConvertFrom-Json` and equivalent JSON checks for plugin metadata/hooks.

Expected: no parse errors.

- [ ] **Step 4: Commit and push**

Run: `git checkout -b chore/sdk-public-mcp-parity`, `git add ...`, `git commit -m "feat: add vscode extension mcp profile support"`, `git push -u origin chore/sdk-public-mcp-parity`.

- [ ] **Step 5: Open PR, wait for CI, merge**

Use GitHub CLI or connector tooling to open the PR, monitor CI, fix any failures, and merge only when checks are green or explicitly non-blocking.
