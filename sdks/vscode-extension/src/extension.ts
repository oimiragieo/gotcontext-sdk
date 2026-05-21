import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";

const MCP_SERVER_BASE_URL = "https://api.gotcontext.ai/mcp";
const DASHBOARD_URL = "https://gotcontext.ai/dashboard";

export type McpProfile = "core" | "full";

export interface McpServerConfig {
  type: "http";
  url: string;
  headers: Record<string, string>;
}

interface McpJson {
  servers: Record<string, McpServerConfig>;
}

interface McpProfilePick extends vscode.QuickPickItem {
  profile: McpProfile;
}

export function mcpServerUrlForProfile(profile: McpProfile): string {
  return `${MCP_SERVER_BASE_URL}?profile=${profile}`;
}

export function buildMcpServerConfig(
  apiKey: string,
  profile: McpProfile = "core",
): McpServerConfig {
  return {
    type: "http",
    url: mcpServerUrlForProfile(profile),
    headers: {
      Authorization: `Bearer ${apiKey.trim()}`,
    },
  };
}

export function activate(context: vscode.ExtensionContext): void {
  // Register "Configure MCP Server" command
  const configureCmd = vscode.commands.registerCommand(
    "gotcontext.configure",
    async () => {
      const apiKey = await vscode.window.showInputBox({
        title: "gotcontext.ai API Key",
        prompt: "Enter your gotcontext.ai API key (starts with gc_)",
        placeHolder: "gc_live_...",
        password: true,
        ignoreFocusOut: true,
        validateInput: (value: string) => {
          const trimmed = value.trim();
          if (!trimmed) {
            return "API key is required";
          }
          if (!trimmed.startsWith("gc_")) {
            return "API key must start with gc_";
          }
          return null;
        },
      });

      if (!apiKey) {
        return; // User cancelled
      }

      const profilePick = await vscode.window.showQuickPick<McpProfilePick>(
        [
          {
            label: "Core (recommended)",
            description: "7 lightweight compression tools",
            detail: "Best default for lower MCP tool-list overhead.",
            profile: "core",
          },
          {
            label: "Full",
            description: "Complete tool catalogue",
            detail: "Use when you need platform tools such as gc_pre_flight.",
            profile: "full",
          },
        ],
        {
          title: "gotcontext.ai MCP Profile",
          placeHolder: "Choose the MCP tool surface for this workspace",
          ignoreFocusOut: true,
        },
      );

      if (!profilePick) {
        return; // User cancelled
      }

      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showErrorMessage(
          "No workspace folder open. Open a folder first, then configure the MCP server.",
        );
        return;
      }

      const workspaceRoot = workspaceFolders[0].uri.fsPath;
      const vscodeDir = path.join(workspaceRoot, ".vscode");
      const mcpJsonPath = path.join(vscodeDir, "mcp.json");

      try {
        // Ensure .vscode directory exists
        if (!fs.existsSync(vscodeDir)) {
          fs.mkdirSync(vscodeDir, { recursive: true });
        }

        // Read existing mcp.json or start fresh
        let mcpConfig: McpJson = { servers: {} };
        if (fs.existsSync(mcpJsonPath)) {
          const existing = fs.readFileSync(mcpJsonPath, "utf-8");
          try {
            mcpConfig = JSON.parse(existing) as McpJson;
            if (!mcpConfig.servers) {
              mcpConfig.servers = {};
            }
          } catch {
            // Malformed JSON — overwrite
            mcpConfig = { servers: {} };
          }
        }

        // Set the gotcontext server entry
        mcpConfig.servers["gotcontext"] = buildMcpServerConfig(
          apiKey,
          profilePick.profile,
        );

        fs.writeFileSync(
          mcpJsonPath,
          JSON.stringify(mcpConfig, null, 2) + "\n",
          "utf-8",
        );

        vscode.window.showInformationMessage(
          `gotcontext MCP server configured in ${mcpJsonPath} (${profilePick.profile} profile)`,
        );
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(
          `Failed to write MCP config: ${message}`,
        );
      }
    },
  );

  // Register "Open Dashboard" command
  const dashboardCmd = vscode.commands.registerCommand(
    "gotcontext.dashboard",
    () => {
      vscode.env.openExternal(vscode.Uri.parse(DASHBOARD_URL));
    },
  );

  // Status bar item
  const statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100,
  );
  statusBarItem.text = "$(cloud) gotcontext";
  statusBarItem.tooltip = "Configure gotcontext.ai MCP Server";
  statusBarItem.command = "gotcontext.configure";
  statusBarItem.show();

  context.subscriptions.push(configureCmd, dashboardCmd, statusBarItem);
}

export function deactivate(): void {
  // Nothing to clean up
}
