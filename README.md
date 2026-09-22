# mcp-jev

Minimal [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes TypeSafe **Jev** (System One) structured decisions to Cursor and other MCP clients.

Jev is the fast classifier; your main LLM is the writer. This server is the bridge: one tool call in, machine-readable yes/no, choice, and score results out.

## Requirements

- Docker and Docker Compose
- A TypeSafe API key from [console.typesafe.ai](https://console.typesafe.ai)

For development and tests only: Python 3.11+

## Quick start (Docker)

Copy `.env.example` to `.env` and set your key (local only — never commit):

```bash
copy .env.example .env
```

Start the MCP HTTP API:

```bash
docker compose up --build -d
```

The server listens at `http://127.0.0.1:8000/mcp` (Streamable HTTP transport).

## MCP client setup

Example configs for Cursor, Claude Code, and Claude Desktop are in [`samples/`](samples/). Copy the one you use — client configs are not committed (only examples).

**Cursor (quick start):**

```bash
mkdir .cursor
copy samples\cursor.mcp.json.example .cursor\mcp.json
```

Start the container before using MCP (`docker compose up -d`). Reload MCP servers after changing `.env`.

See [`samples/README.md`](samples/README.md) for Claude Code and Claude Desktop paths and notes.

## Local development (optional)

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[dev]"
pytest
```

Run without Docker (stdio transport, for MCP Inspector):

```bash
set JEV_TRANSPORT=stdio
python -m mcp_jev.server
```

Or HTTP on the host (matches Docker behavior):

```bash
set JEV_TRANSPORT=streamable-http
set JEV_HOST=127.0.0.1
python -m mcp_jev.server
```

## Tool: `jev_decide`

Evaluate a `state` against one or more typed `questions` using TypeSafe Jev. Returns probabilities and structured answers — not natural language.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | string, object, or array | yes | Content Jev judges. Prefer a JSON object with named fields. |
| `questions` | object | yes | Map of question id → question definition. |
| `model` | string | no | Default `jev-latest`. Pin e.g. `jev-1.13.0` when tuning thresholds. |

### Question types

| Type | Purpose | Required fields |
|------|---------|-----------------|
| `noul` | Yes/no probability | `instructions`; optional `criteria` `{ "true", "false" }` |
| `choice` | Pick one option | `instructions`, `criteria` (map option → description) |
| `score` | Ordered scale | `instructions`, `criteria` (array, low → high, 2–10 levels) |

### Example

```json
{
  "state": {
    "message": "My card was charged twice for order A-104."
  },
  "questions": {
    "is_billing": {
      "type": "noul",
      "instructions": "Is `message` about billing or payments?"
    },
    "department": {
      "type": "choice",
      "instructions": "Which team should handle `message`?",
      "criteria": {
        "billing": "Charges, invoices, refunds",
        "technical": "Bugs or outages",
        "other": "None of the above"
      }
    }
  }
}
```

Success response (pretty-printed JSON string):

```json
{
  "model": "jev-1.13.0",
  "answers": { },
  "usage": { "input_tokens": 0, "output_tokens": 0 }
}
```

On failure, the tool returns a structured error object instead of throwing:

```json
{
  "error": true,
  "status": 422,
  "message": "Validation failed: ...",
  "details": { }
}
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TYPESAFE_API_KEY` | yes | — | Bearer token from TypeSafe console |
| `JEV_TRANSPORT` | no | `stdio` (`streamable-http` in Docker) | MCP transport |
| `JEV_HOST` | no | `127.0.0.1` (`0.0.0.0` in Docker) | HTTP bind address |
| `JEV_PORT` | no | `8000` | HTTP port |
| `JEV_HTTP_PATH` | no | `/mcp` | Streamable HTTP endpoint path |
| `JEV_STATELESS_HTTP` | no | `true` | Stateless HTTP sessions |
| `JEV_DEFAULT_MODEL` | no | `jev-latest` | Default model for tool calls |
| `JEV_API_BASE` | no | `https://api.typesafe.ai` | API base URL (testing/mocking) |
| `JEV_TIMEOUT_SEC` | no | `30` | Per-request HTTP timeout |
| `JEV_MAX_RETRIES` | no | `3` | Retries for HTTP 429/529 |

## Limits

Documented by TypeSafe; lightly validated locally in v1:

| Limit | Value |
|-------|-------|
| State + all questions (combined) | ~64,000 tokens |
| State + longest single question | ~32,000 tokens |
| Choice options | up to 255 |
| Score levels | 2–10 |

## Testing

```bash
pytest
```

Tests mock HTTP — no API key required.

### Manual smoke test

1. Set `TYPESAFE_API_KEY` in `.env`.
2. Run `docker compose up --build -d`.
3. Open Cursor and call `jev_decide` with one `noul` question on a short string.
4. Confirm `answers.*.noul` is a float in `[0, 1]`.

## Security

- Never log or commit `TYPESAFE_API_KEY`.
- Treat `state` as potentially sensitive — nothing is persisted in v1.
- Threshold and routing logic belong in the agent prompt, not in this server.

## Disclaimer

Unofficial project. Not affiliated with, endorsed by, or sponsored by TypeSafe, Anthropic, or the Model Context Protocol project. **Jev**, **TypeSafe**, **Model Context Protocol**, **Cursor**, and **Claude** are trademarks of their respective owners.

## License

[MIT](LICENSE) — use, modify, and distribute freely.

## References

- [TypeSafe — Introducing System One and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
