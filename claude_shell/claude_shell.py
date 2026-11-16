"""
claude_shell.py — Sankofa Tools
Claude Shell v0.5 (skeleton toward v1.0)

Build log:
  v0.1 — M2: functions, basic API call, terminal loop
  v0.2 — M3+M4: conversation history (list of dicts), .env loading, session log
  v0.3 — M5: error handling around client.messages.create(), (text, error) contract
  v0.4 — M6: ClaudeShell class — ask(), ask_with_search(), log_turn()
  v0.5 — M7 skeleton: ask_stream(), export_json(), parse_args() are stubs to fill in.
         The file runs as-is; nothing new is wired into run() until you swap it in.
  v1.0 — streaming + configurable system prompt + JSON export + README
"""

import argparse
import json
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

SESSION_LOG = "session_log.txt"
MODEL = "claude-sonnet-4-6"


def get_client():
    """Return an authenticated Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Check your .env file.")
    return anthropic.Anthropic(api_key=api_key)


class ClaudeShell:
    def __init__(self, system_prompt=None, log_path=SESSION_LOG):
        self.client = get_client()
        self.history = []
        self.system_prompt = system_prompt
        self.log_path = log_path

    # ── UNCHANGED from v0.4 ───────────────────────────────

    def ask(self, user_input):
        """
        Send a plain conversational turn. Appends to self.history.

        Returns:
            (response_text, error_message) tuple.
            On success: (text, None). On API failure: (None, error string).
        """
        self.history.append({"role": "user", "content": user_input})

        kwargs = {
            "model": MODEL,
            "max_tokens": 1024,
            "messages": self.history,
        }
        if self.system_prompt:
            kwargs["system"] = self.system_prompt

        try:
            response = self.client.messages.create(**kwargs)
        except anthropic.APIError as e:
            self.history.pop()
            return None, str(e)

        response_text = response.content[0].text
        self.history.append({"role": "assistant", "content": response_text})
        return response_text, None

    def ask_with_search(self, query):
        """
        Send a turn with the web_search tool enabled. Appends to self.history
        like ask() does. Used by snkf_protocol/run_protocol.py.

        Returns:
            (summary_text, citations, error_message) tuple.
        """
        self.history.append({"role": "user", "content": query})

        kwargs = {
            "model": MODEL,
            "max_tokens": 1024,
            "messages": self.history,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        }
        if self.system_prompt:
            kwargs["system"] = self.system_prompt

        try:
            response = self.client.messages.create(**kwargs)
        except anthropic.APIError as e:
            self.history.pop()
            return None, [], str(e)

        text_parts = []
        citations = []
        seen_urls = set()

        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_parts.append(block.text)
                for c in getattr(block, "citations", None) or []:
                    url = getattr(c, "url", None)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        citations.append({
                            "title": getattr(c, "title", url),
                            "url": url,
                        })
            elif block_type == "web_search_tool_result":
                for result in getattr(block, "content", None) or []:
                    url = getattr(result, "url", None)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        citations.append({
                            "title": getattr(result, "title", url),
                            "url": url,
                        })

        summary_text = "\n".join(text_parts)
        self.history.append({"role": "assistant", "content": summary_text})
        return summary_text, citations, None

    def log_turn(self, user_input, response_text=None, error=None):
        """Append one turn to the session log. Best-effort: never crashes the shell."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_path, "a") as f:
                if error:
                    f.write(f"[{timestamp}] ERROR: {error}\n")
                else:
                    f.write(f"[{timestamp}] You: {user_input}\n")
                    f.write(f"[{timestamp}] Claude: {response_text}\n")
        except OSError as e:
            print(f"[Warning: could not write to session log — {e}]")

    # ── NEW: YOU WRITE THESE ──────────────────────────────

    def ask_stream(self, user_input):
        """
        Like ask(), but prints text as it arrives instead of all at once.

        Must keep the same contract as ask(): return (full_text, error).

        TODO 1: append the user turn to self.history (same as ask()).
        TODO 2: build kwargs the same way ask() does (model, max_tokens,
                messages, optional system).
        TODO 3: open a streaming call with a `with` block:
                    with self.client.messages.stream(**kwargs) as stream:
                and loop over stream.text_stream. For each chunk: print it
                with end="" and flush=True, and collect it in a list.
        TODO 4: after the loop, join the chunks into full_text, print a
                newline, append the assistant turn to self.history, and
                return (full_text, None).
        TODO 5: wrap the whole thing in try/except anthropic.APIError.
                On failure, roll back the user turn exactly like ask() does,
                and return (None, str(e)).

        Question to answer before you run it: if the connection drops halfway
        through a response, what is in your chunk list, and should any of it
        be written to history?
        """
        raise NotImplementedError("ask_stream: fill in TODOs 1-5")

    def export_json(self, path):
        """
        Write the session to a JSON file.

        TODO 1: build a dict with at least: "exported" (ISO timestamp),
                "model", "system_prompt", and "messages" (self.history).
        TODO 2: open `path` for writing inside a `with` block and use
                json.dump(..., indent=2).
        TODO 3: wrap the file I/O in try/except OSError, same
                best-effort pattern as log_turn(). Return True or False
                so the caller knows whether it worked.
        """
        raise NotImplementedError("export_json: fill in TODOs 1-3")


def parse_args():
    """
    TODO 1: create an argparse.ArgumentParser with a short description.
    TODO 2: add --system (string, default None): the system prompt text.
    TODO 3: add --export (string, default None): path to write JSON on exit.
    TODO 4: add --no-stream (flag, action="store_true"): fall back to ask().
    TODO 5: return parser.parse_args()
    """
    raise NotImplementedError("parse_args: fill in TODOs 1-5")


def print_response(text):
    """Format and print Claude's response (non-streaming path)."""
    print(f"\nClaude: {text}\n")


# ── Main loop (still the v0.4 behavior until you swap pieces in) ──

def run():
    print("── Claude Shell v0.5 ──────────────────────────")
    print("Type your message. 'quit' or Ctrl+C to exit.")
    print("───────────────────────────────────────────────\n")

    # TODO (after parse_args works): args = parse_args()
    #   shell = ClaudeShell(system_prompt=args.system)
    shell = ClaudeShell()

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

        # TODO (after ask_stream works): if not args.no_stream, call
        #   print("\nClaude: ", end="")
        #   response, error = shell.ask_stream(user_input)
        # and skip print_response() since the text already printed live.
        response, error = shell.ask(user_input)
        if error:
            print(f"\n[API error — turn not saved to history]: {error}\n")
            shell.log_turn(user_input, error=error)
            continue
        print_response(response)
        shell.log_turn(user_input, response_text=response)

    # TODO (after export_json works): if args.export, call
    #   shell.export_json(args.export) and report whether it succeeded.


if __name__ == "__main__":
    run()
