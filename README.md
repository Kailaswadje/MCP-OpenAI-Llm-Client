# 🔌 MCP + OpenAI — Building an LLM Client That Discovers and Calls MCP Tools

A minimal, end-to-end example of the **Model Context Protocol (MCP)**: a FastMCP server exposes Python functions as tools, and a custom client connects over **stdio**, discovers those tools at runtime, hands them to **OpenAI `gpt-4o-mini`** as function definitions, and executes whichever tool the LLM chooses.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-1.29.0-black)
![FastMCP](https://img.shields.io/badge/Server-FastMCP-orange)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)
![Transport](https://img.shields.io/badge/Transport-stdio-lightgrey)

---

## 📌 Overview

MCP is an open standard for connecting LLM applications to tools and data. Instead of hardcoding tool definitions inside your app, an **MCP server** advertises what it can do, and any **MCP client** can discover and use it.

This project builds both sides from scratch:

| Component | File | Role |
|---|---|---|
| 🛠️ MCP Server | `llmserver.py` | Exposes `add_numbers` and `multiply_numbers` as MCP tools via FastMCP |
| 🤖 MCP Client | `llmclient.py` | Launches the server, lists its tools, lets OpenAI pick one, runs it |

The key idea: **the client never hardcodes the tools.** It asks the server what exists, converts that into OpenAI's function-calling format, and lets the LLM decide.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      llmclient.py (MCP Client)               │
│                                                              │
│  1. Launch server  ──►  StdioServerParameters("python",      │
│                          ["llmserver.py"])                   │
│  2. session.initialize()                                     │
│  3. session.list_tools()  ──►  [add_numbers, multiply_numbers]│
│  4. Convert MCP inputSchema  ──►  OpenAI "parameters"        │
│  5. OpenAI gpt-4o-mini + tools  ──►  tool_call chosen        │
│  6. session.call_tool(name, arguments)                       │
│  7. Print result.structuredContent["result"]                 │
└───────────────────────────┬──────────────────────────────────┘
                            │  stdio (JSON-RPC)
┌───────────────────────────▼──────────────────────────────────┐
│                      llmserver.py (FastMCP Server)           │
│     @mcp.tool() add_numbers(a, b)                            │
│     @mcp.tool() multiply_numbers(a, b)                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
MCP-OpenAI-Llm-Client/
├── llmserver.py       # FastMCP server exposing math tools
├── llmclient.py       # MCP client + OpenAI function calling
├── requirements.txt   # mcp, openai, python-dotenv
├── .env.example       # Template for your OpenAI API key
├── .gitignore         # Ignores .env, venv, caches
└── README.md          # This file
```

---

## 🛠️ Part 1 — The MCP Server (`llmserver.py`)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My First MCP Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

if __name__ == "__main__":
    mcp.run()
```

FastMCP turns ordinary Python into a fully described tool — no manual schema writing:

| Python | Becomes in MCP |
|---|---|
| Function name | Tool name |
| Docstring | Tool description |
| Type hints (`a: int, b: int`) | JSON input schema |
| Return value | Tool result (`structuredContent["result"]`) |

`mcp.run()` defaults to **stdio** transport, so the server talks over stdin/stdout — which is exactly how the client launches and talks to it.

---

## 🤖 Part 2 — Connecting & Discovering Tools at Runtime

```python
server_params = StdioServerParameters(command="python", args=["llmserver.py"])

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

- `stdio_client` **spawns the server as a subprocess** — you don't run it separately
- `initialize()` performs the MCP handshake
- `list_tools()` returns each tool's `name`, `description` and `inputSchema`

---

## 🔄 Part 3 — Translating MCP Tools into OpenAI Function Definitions

MCP and OpenAI both describe arguments with JSON Schema, so the bridge is a straight mapping:

```python
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        },
    }
    for tool in tools.tools
]
```

This is the heart of the project: **any** MCP server's tools can be plugged into OpenAI this way, without changing client code.

---

## 🧠 Part 4 — Let the LLM Choose, Then Execute via MCP

```python
response = llm.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": user_query}],
    tools=openai_tools,
)
message = response.choices[0].message

if message.tool_calls:
    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_arguments = json.loads(tool_call.function.arguments)
    result = await session.call_tool(tool_name, arguments=tool_arguments)
    print(result.structuredContent["result"])
else:
    print(message.content)
```

The LLM **reasons** about which tool fits the question and produces the arguments; the MCP server **executes** it. Responsibilities stay cleanly separated.

---

## 📟 Example Output

For the query `"What is 10 + 20?"`:

```
Connected to MCP server
Available MCP Tools:
 - add_numbers
 - multiply_numbers
LLM selected tool: add_numbers
Arguments: {'a': 10, 'b': 20}
MCP Tool Result: 30
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Installation

```bash
git clone https://github.com/Kailaswadje/MCP-OpenAI-Llm-Client.git
cd MCP-OpenAI-Llm-Client

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure your key

```bash
cp .env.example .env
# then edit .env:
OPENAI_API_KEY=your-key-here
```

### Run

```bash
python llmclient.py
```

You only run the **client** — it starts `llmserver.py` automatically over stdio.

> ⚠️ `.env` is in `.gitignore`. Never commit your real API key.

---

## 💡 Key Takeaways

- **MCP decouples tools from the app** — servers advertise capabilities, clients discover them
- **FastMCP removes boilerplate** — docstrings and type hints become tool metadata
- **stdio transport is the simplest setup** — the client owns the server's lifecycle
- **MCP schemas map 1:1 to OpenAI function calling** — one small loop bridges the two ecosystems
- **The LLM decides, the server executes** — a clean separation that scales to real tools (APIs, databases, files)

---

## ⚠️ Current Limitations

- **Single turn** — the tool result is printed but not sent back to the LLM for a natural-language final answer
- **Hardcoded query** — `user_query` is fixed to `"What is 10 + 20?"`
- **Only the first tool call is handled** — parallel tool calls are ignored
- **Toy tools** — integer-only math to keep the protocol in focus
- Minor cleanup: `OpenAI` is imported twice and `llm = OpenAI()` is created twice in `llmclient.py`

---

## 🔮 Possible Extensions

- [ ] Send the tool result back as a `role: "tool"` message so the LLM writes the final answer
- [ ] Add a loop so the LLM can chain multiple tool calls (e.g. *"add 10 and 20, then multiply by 3"*)
- [ ] Replace the hardcoded query with `input()` for an interactive CLI
- [ ] Add real-world tools — weather API, SQL queries, file search
- [ ] Switch to Streamable HTTP transport to run the server remotely
- [ ] Reuse the same server inside Claude Desktop or other MCP-compatible hosts

---

## 📚 References

- [Model Context Protocol — Official Docs](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

---

## 👤 Author

**Kailas Wadje**
MSc Data Science & AI, University of Liverpool

- GitHub: [@Kailaswadje](https://github.com/Kailaswadje)
- LinkedIn: [linkedin.com/in/kwadaje](https://www.linkedin.com/in/kwadaje/)

---

⭐ If this helped you understand MCP, consider giving it a star!
