"""
claude_shell.py — Sankofa Tools
Claude Shell v0.1

Build-first scaffold. Each phase of M2–M7 adds a feature.
Current: M2 Functions — send_message() and get_response() wired up.

Build log:
  v0.1 — M2: functions, basic API call, terminal loop
  v0.2 — M3+M4: conversation history (list of dicts), .env loading
  v0.3 — M5: error handling, response parsing, session file logging
  v0.4 — M6: refactor into ClaudeShell class
  v1.0 — M7: async streaming, system prompt config, JSON export
"""

import os
import anthropic
from dotenv import load_dotenv  # pip install python-dotenv

# ── M4: Load API key from .env ────────────────────────────
# Create a .env file in this directory with: ANTHROPIC_API_KEY=sk-...
# Never hardcode the key. Never commit .env to git.
load_dotenv()


# ── M2: Core functions ────────────────────────────────────

def get_client():
    """Return an authenticated Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Check your .env file.")
    return anthropic.Anthropic(api_key=api_key)


def send_message(client, history, user_input, system_prompt=None):
    """
    Send a message to Claude and return the full response text.

    Args:
        client: Anthropic client instance
        history: list of {"role": ..., "content": ...} dicts  ← M3
        user_input: string from the user
        system_prompt: optional string to set Claude's behavior

    Returns:
        response text as a string
    """
    # M3: append user message to history
    history.append({"role": "user", "content": user_input})

    # Build kwargs — system prompt is optional
    kwargs = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": history,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    # M5: wrap in try/except when that module is drilled
    response = client.messages.create(**kwargs)
    response_text = response.content[0].text

    # M3: append assistant response to history
    history.append({"role": "assistant", "content": response_text})

    return response_text


def print_response(text):
    """Format and print Claude's response."""
    print(f"\nClaude: {text}\n")


# ── M3: Conversation history ──────────────────────────────
# history is a list of dicts: [{"role": "user", "content": "..."}, ...]
# It grows with every turn. Pass it into send_message() each time.
# This is what makes the conversation multi-turn.

def init_history():
    """Return a fresh, empty conversation history."""
    return []


# ── Main loop ─────────────────────────────────────────────

def run():
    """Run the Claude Shell conversation loop."""
    print("── Claude Shell v0.1 ──────────────────────────")
    print("Type your message. 'quit' or Ctrl+C to exit.")
    print("───────────────────────────────────────────────\n")

    client = get_client()
    history = init_history()

    # Optional: set a system prompt to shape Claude's behavior
    # system_prompt = "You are a concise technical assistant."
    system_prompt = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break

        # M5 TODO: wrap this in try/except for API errors
        response = send_message(client, history, user_input, system_prompt)
        print_response(response)

        # M4 TODO: write session to file after each turn
        # M6 TODO: refactor this loop into ClaudeShell class
        # M7 TODO: replace send_message with async streaming version


if __name__ == "__main__":
    run()
