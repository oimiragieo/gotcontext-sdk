import { describe, expect, it, vi } from "vitest";

vi.mock("vscode", () => ({}));

const { buildMcpServerConfig, mcpServerUrlForProfile } =
  await import("./extension");

describe("MCP profile URLs", () => {
  it("defaults new installs to the lightweight core profile", () => {
    expect(mcpServerUrlForProfile("core")).toBe(
      "https://api.gotcontext.ai/mcp?profile=core",
    );
  });

  it("supports the full profile for platform tools", () => {
    expect(mcpServerUrlForProfile("full")).toBe(
      "https://api.gotcontext.ai/mcp?profile=full",
    );
  });

  it("writes the selected profile URL and bearer header", () => {
    expect(buildMcpServerConfig("gc_live_test", "core")).toEqual({
      type: "http",
      url: "https://api.gotcontext.ai/mcp?profile=core",
      headers: { Authorization: "Bearer gc_live_test" },
    });
  });
});
