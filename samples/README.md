# MCP client examples

Start the server first:

```bash
docker compose up -d
```

Secrets stay in the repo `.env` (for Compose). None of these client files need `TYPESAFE_API_KEY`.

| Client | Example file | Install to |
|--------|--------------|------------|
| **Cursor** | [`cursor.mcp.json.example`](cursor.mcp.json.example) | `.cursor/mcp.json` in this repo |
| **Claude Code** | [`claude-code.mcp.json.example`](claude-code.mcp.json.example) | `.mcp.json` in this repo |
| **Claude Desktop** | [`claude-desktop.config.json.example`](claude-desktop.config.json.example) | See paths below |

## Cursor

```bash
mkdir .cursor
copy samples\cursor.mcp.json.example .cursor\mcp.json
```

Reload MCP servers in Cursor after `docker compose up`.

## Claude Code

Claude Code requires `"type": "http"` on URL-based servers.

```bash
copy samples\claude-code.mcp.json.example .mcp.json
```

## Claude Desktop

Claude Desktop does not accept a bare `url` in its JSON config for local servers. Use the `mcp-remote` bridge (requires Node.js/npx).

Merge [`claude-desktop.config.json.example`](claude-desktop.config.json.example) into:

| OS | Path |
|----|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Fully quit and reopen Claude Desktop after editing.
