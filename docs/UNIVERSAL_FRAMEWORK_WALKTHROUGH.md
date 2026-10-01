# Universal Antigravity Agent Framework — Complete Blueprint & Walkthrough

This document defines a **universal, interface-agnostic framework architecture** for building any custom application (REST API, Web Frontend, Telegram Bot, Discord Bot, CLI Tool, or IDE Extension) powered by your **local Antigravity subscription quota** without relying on billed third-party API keys.

---

## 1. High-Level Architecture Overview

The framework separates application logic into three decoupled layers:

```mermaid
graph TD
    subgraph Layer 1: Client Adapters (Pluggable UI/API)
        REST["REST API / FastAPI"]
        WebSockets["WebSocket Server"]
        ChatBots["Chat Platforms (Telegram/Discord/Slack)"]
        CLI["CLI Tool / Terminal"]
    end

    subgraph Layer 2: Core Agent Engine (Framework Core)
        SessionManager["Session & State Manager (session.py)"]
        AgentClient["Universal Agent Client (agent.py)"]
        ToolExecutor["Host System Tools (tools.py)"]
    end

    subgraph Layer 3: Antigravity Subsystem (Local OS)
        AGY_CLI["agy.exe agentapi (Local CLI)"]
        BrainLogs["Session Logs (~/.gemini/antigravity/brain/)"]
        HostOS["Host Operating System"]
    end

    REST --> AgentClient
    WebSockets --> AgentClient
    ChatBots --> AgentClient
    CLI --> AgentClient

    AgentClient -->|Spawn CLI Command| AGY_CLI
    AgentClient -->|Poll Response| BrainLogs
    AGY_CLI -->|Execute System Tools| ToolExecutor
    ToolExecutor -->|Perform File/CMD Ops| HostOS
    ToolExecutor -->|Return Result| BrainLogs
    BrainLogs -->|Final Output| AgentClient
```

### Key Framework Principles
1. **Interface Agnostic**: The core agent client operates independently of the frontend (HTTP, WebSockets, IPC, CLI, or Chat platforms).
2. **Zero Provider Token Costs**: Routes requests through the local `agy.exe agentapi` CLI wrapper, consuming your active subscription quota rather than billed API endpoints.
3. **Pluggable OS Tools**: Exposes local OS commands (`run_command`, `read_file`, `write_file`, `edit_file`, `list_dir`) directly to the agent.
4. **Isolated Session Management**: Manages state, conversation IDs, system instructions, and response polling cleanly.

---

## 2. Universal Directory Structure

```
antigravity_agent_framework/
├── core/
│   ├── __init__.py
│   ├── config.py           # Universal configuration & environment handler
│   ├── agent.py            # Generic AntigravityAgentClient (CLI wrapper & log poller)
│   ├── tools.py            # Local OS tool primitive definitions
│   └── session.py          # Session state & conversation lifecycle manager
├── adapters/
│   ├── rest_api.py         # FastAPI / Flask REST adapter
│   ├── websocket_server.py # Real-time WebSocket streaming adapter
│   ├── cli_client.py       # Terminal interactive CLI adapter
│   └── chat_bot.py         # Generic messaging bot adapter (Discord/Telegram/Slack)
└── .env.example            # Configuration template
```

---

## 3. Core Engine Implementation

### 3.1 Universal Configuration (`core/config.py`)

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

class Config:
    # Path to agy.exe CLI executable
    AGY_PATH = os.getenv("AGY_PATH", os.path.expandvars(r'%LOCALAPPDATA%\agy\bin\agy.exe'))
    
    # Path to local Antigravity brain directory storing session logs
    BRAIN_DIR = os.getenv("BRAIN_DIR", os.path.join(os.path.expanduser('~'), '.gemini', 'antigravity', 'brain'))
    
    # Default model configuration ('pro' or 'flash')
    DEFAULT_MODEL = os.getenv("AGENT_MODEL", "pro")
    
    # Default timeout for agent execution in seconds
    EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", "300"))
```

---

### 3.2 System Execution Tools (`core/tools.py`)

```python
import os
import subprocess

def run_command(command: str) -> str:
    """Executes a terminal command on the host OS."""
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        return f"Exit Code: {res.returncode}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    except Exception as e:
        return f"Execution Error: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads file content from the host filesystem."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Read Error: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a specified path on the host filesystem."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Write Error: {str(e)}"

def edit_file(filepath: str, target_text: str, replacement_text: str) -> str:
    """Replaces exact target string inside a file."""
    try:
        content = read_file(filepath)
        if target_text not in content:
            return f"Error: Target text not found in {filepath}"
        new_content = content.replace(target_text, replacement_text)
        return write_file(filepath, new_content)
    except Exception as e:
        return f"Edit Error: {str(e)}"

def list_dir(dirpath: str) -> str:
    """Lists directory contents."""
    try:
        return "\n".join(os.listdir(dirpath))
    except Exception as e:
        return f"List Error: {str(e)}"
```

---

### 3.3 Generic Agent Client (`core/agent.py`)

This client handles conversation creation, subprocess execution, log transcript polling, and step evaluation independent of the UI layer.

```python
import os
import subprocess
import json
import time
from typing import Optional, Dict, Any
from core.config import Config

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are Antigravity, an advanced agentic AI assistant. You have full system tool access.\n"
    "Execute terminal commands, read files, write files, and edit files directly to accomplish tasks.\n"
    "Provide clear, concise, and structured answers."
)

class AntigravityAgentClient:
    def __init__(self, system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION, model: str = None):
        self.conversation_id: Optional[str] = None
        self.system_instruction = system_instruction
        self.model = model or Config.DEFAULT_MODEL
        self.agy_path = Config.AGY_PATH
        self.brain_dir = Config.BRAIN_DIR

    def reset_session(self) -> None:
        """Resets the current conversation context."""
        self.conversation_id = None

    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Sends a prompt to the agent and polls transcript log for the final response.
        Returns a dict containing response status, content, and conversation_id.
        """
        try:
            transcript_path = None
            initial_line_count = 0

            if self.conversation_id:
                transcript_path = os.path.join(
                    self.brain_dir, self.conversation_id, ".system_generated", "logs", "transcript_full.jsonl"
                )
                if os.path.exists(transcript_path):
                    with open(transcript_path, 'r', encoding='utf-8') as f:
                        initial_line_count = len(f.readlines())

            # Formulate CLI command
            if not self.conversation_id:
                full_prompt = f"[System Instruction]\n{self.system_instruction}\n\n[User Request]\n{message}"
                cmd = [
                    self.agy_path, "agentapi", "new-conversation",
                    f"--model={self.model}", "--title=Agent Session", full_prompt
                ]
            else:
                cmd = [
                    self.agy_path, "agentapi", "send-message",
                    self.conversation_id, message
                ]

            # Execute CLI invocation
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = json.loads(res.stdout)

            if not self.conversation_id:
                self.conversation_id = output["response"]["newConversation"]["conversationId"]
                transcript_path = os.path.join(
                    self.brain_dir, self.conversation_id, ".system_generated", "logs", "transcript_full.jsonl"
                )
                initial_line_count = 0

            # Poll transcript log until completion
            start_time = time.time()
            while time.time() - start_time < Config.EXECUTION_TIMEOUT:
                if os.path.exists(transcript_path):
                    with open(transcript_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i in range(initial_line_count, len(lines)):
                        try:
                            step = json.loads(lines[i])
                            if (
                                step.get("source") == "MODEL"
                                and step.get("type") == "PLANNER_RESPONSE"
                                and step.get("status") == "DONE"
                                and not step.get("tool_calls")
                            ):
                                return {
                                    "success": True,
                                    "content": step.get("content", ""),
                                    "conversation_id": self.conversation_id
                                }
                        except Exception:
                            pass
                time.sleep(0.5)

            return {"success": False, "error": "Execution timeout exceeded.", "conversation_id": self.conversation_id}

        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"CLI Execution Failure: {e.stderr or e.stdout or str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Agent Error: {str(e)}"}
```

---

## 4. Pluggable Client Adapters

### 4.1 REST API Adapter (`adapters/rest_api.py` - FastAPI)

Exposes the agent as a clean HTTP service for web applications, mobile apps, or microservices.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.agent import AntigravityAgentClient

app = FastAPI(title="Antigravity Agent REST API")
agent = AntigravityAgentClient()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    success: bool
    response: str
    conversation_id: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    result = agent.send_message(req.message)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return ChatResponse(
        success=True,
        response=result["content"],
        conversation_id=result["conversation_id"]
    )

@app.post("/api/reset")
async def reset_endpoint():
    agent.reset_session()
    return {"message": "Session reset successfully"}
```

---

### 4.2 Interactive CLI Adapter (`adapters/cli_client.py`)

A lightweight terminal interface for developers.

```python
from core.agent import AntigravityAgentClient

def main():
    agent = AntigravityAgentClient()
    print("=== Antigravity Interactive Terminal Agent ===")
    print("Type 'exit' to quit, '/reset' to reset session.\n")

    while True:
        try:
            user_input = input("\nUser > ").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                break
            if user_input.lower() == "/reset":
                agent.reset_session()
                print("🔄 Session reset.")
                continue

            print("Agent is processing...")
            res = agent.send_message(user_input)
            if res["success"]:
                print(f"\nAgent > {res['content']}")
            else:
                print(f"\nError > {res['error']}")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
```

---

### 4.3 WebSocket Real-Time Adapter (`adapters/websocket_server.py`)

Enables real-time bidirectional streaming for modern web frontends (React / Next.js / Vue).

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from core.agent import AntigravityAgentClient

app = FastAPI()

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    agent = AntigravityAgentClient()
    
    try:
        while True:
            prompt = await websocket.receive_text()
            if prompt.strip() == "/reset":
                agent.reset_session()
                await websocket.send_json({"type": "reset", "status": "ok"})
                continue
                
            res = agent.send_message(prompt)
            await websocket.send_json({"type": "response", "data": res})
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
```

---

## 5. Output Buffering & Chunking Strategy

Different platforms enforce distinct payload constraints:
- **Discord**: Max 2,000 characters per message
- **Telegram**: Max 4,096 characters per message
- **WebSockets / REST**: Unlimited / Streamed chunks

Implement a generic chunker utility:

```python
def format_and_chunk(text: str, max_chars: int = 1900) -> list[str]:
    """Generic text chunker that preserves Markdown code blocks across splits."""
    chunks = []
    current_chunk, current_len, in_codeblock = [], 0, False

    for line in text.splitlines(keepends=True):
        if "```" in line:
            in_codeblock = not in_codeblock

        if current_len + len(line) > max_chars:
            if in_codeblock:
                current_chunk.append("```\n")
            chunks.append("".join(current_chunk))
            current_chunk = ["```\n" + line] if in_codeblock else [line]
            current_len = len(current_chunk[0])
        else:
            current_chunk.append(line)
            current_len += len(line)

    if current_chunk:
        chunks.append("".join(current_chunk))
    return chunks
```

---

## 6. Framework Summary

By separating **Core Engine Logic** ([agent.py](file:///C:/Users/ICAS/.gemini/antigravity/scratch/discord_antigravity_bridge/agent.py#L16), [tools.py](file:///C:/Users/ICAS/.gemini/antigravity/scratch/discord_antigravity_bridge/tools.py#L1)) from **Interface Adapters**, this architecture allows you to connect any frontend or service to your local Antigravity subscription engine seamlessly.
