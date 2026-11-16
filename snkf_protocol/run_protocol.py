"""
run_protocol.py — Sankofa Tools
SNKF Protocol Runner v0.2

Runs the weekly ecosystem scan or monthly plan review from the terminal.
v0.2: the weekly scan is AI-assisted — ClaudeShell.ask_with_search() fetches
and summarizes each source, suggests a signal level, and you review/override
before it's logged. Monthly review stays fully manual (the judgment layer).

Usage:
    python3 run_protocol.py          # prompts you to choose scan or review
    python3 run_protocol.py --scan   # weekly ecosystem scan
    python3 run_protocol.py --review # monthly plan review

v0.1 — no API calls, pure CLI workflow
v0.2 — AI-assist layer: ClaudeShell.ask_with_search() fetches + summarizes
       each weekly checkpoint, suggests a signal (g/y/r/n), human reviews
       and can override before logging — HITL by design, not autopilot
"""

import sys
import os
import datetime

# claude_shell.py lives in a sibling directory: sankofa-tools/claude_shell/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "claude_shell"))
from claude_shell import ClaudeShell


# ── Config ────────────────────────────────────────────────

SIGNAL_LEVELS = {
    "g": ("green",  "Note it, no plan change"),
    "y": ("yellow", "Discuss, maybe adjust"),
    "r": ("red",    "Act now"),
    "n": ("none",   "Nothing flagged"),
}

WEEKLY_CHECKPOINTS = [
    {
        "id": "anthropic",
        "label": "Anthropic blog + changelog",
        "hint": "anthropic.com/news — new models, API changes, new features",
    },
    {
        "id": "simon",
        "label": "Simon Willison's blog",
        "hint": "simonwillison.net — best signal-to-noise ratio in the LLM space",
    },
    {
        "id": "linkedin",
        "label": "LinkedIn — 'applied AI engineer' jobs",
        "hint": "Note any new required skills, tools, or frameworks you haven't seen before",
    },
    {
        "id": "github",
        "label": "GitHub Trending — Python + AI/LLM",
        "hint": "New repos with 500+ stars in a week often signal an ecosystem shift",
    },
    {
        "id": "aws",
        "label": "AWS What's New — AI/ML section",
        "hint": "aws.amazon.com/new — Bedrock updates, model availability, cert announcements",
    },
    {
        "id": "signal_log",
        "label": "Signal log",
        "hint": "What did you flag across all five sources? One note per signal.",
    },
]

MONTHLY_CHECKPOINTS = [
    {
        "id": "certs",
        "label": "Cert sequence review",
        "hint": "Any retirements, new certs, exam changes? Especially AIF-C01 and DL.AI",
    },
    {
        "id": "projects",
        "label": "Project list review",
        "hint": "Any now obsolete? Any new gap to fill? If a tool is default in every framework, the project loses signal",
    },
    {
        "id": "tech_stack",
        "label": "Tech stack review",
        "hint": "New Anthropic SDK version, new LangGraph patterns, new AWS SDK behaviors",
    },
    {
        "id": "job_market",
        "label": "Job market review",
        "hint": "Title trends shifting? Track 'applied AI engineer', 'eval engineer', 'LLM engineer'",
    },
    {
        "id": "plan_version",
        "label": "Plan version update",
        "hint": "Bump v9.x → v9.(x+1) if anything changed. Log what changed and why",
    },
    {
        "id": "dashboard_sync",
        "label": "Dashboard sync",
        "hint": "Keep heatmap week count synced with actual current week in the plan",
    },
]


# ── M6/v0.2: AI-assist config ─────────────────────────────

SCAN_SYSTEM_PROMPT = (
    "You are running the Sankofa Weekly Intelligence Scan for Damon Collins, "
    "an independent applied AI practitioner building toward freelance work in "
    "AI/ML, with HITL (human-in-the-loop) and evaluation engineering as his "
    "core specialization. For each source you're asked to search, find "
    "genuinely new developments from roughly the past 7 days — skip anything "
    "older or generic. Summarize in 3-5 concise sentences, prioritizing "
    "items relevant to applied AI engineering, HITL, evals, agentic systems, "
    "or AWS AI/ML tooling. Classify the urgency of what you found using this "
    "scale: g=green (note it, no plan change), y=yellow (worth discussing, "
    "may need a plan adjustment), r=red (act now — e.g. a cert retiring, a "
    "tool obsoleting a planned project), n=none (nothing new or relevant "
    "found). End your response with exactly one line in this format: "
    "'SIGNAL: <code>' using one of g, y, r, n."
)


def build_query(checkpoint):
    """Turn a checkpoint's label/hint into a search query for ask_with_search()."""
    return (
        f"{checkpoint['label']}. {checkpoint['hint']}. "
        f"Focus on the most recent developments from the last week."
    )


def parse_signal(text):
    """
    Extract the trailing 'SIGNAL: <code>' line the AI is instructed to
    include. Tolerant of markdown emphasis (**SIGNAL: g**) and full words
    (SIGNAL: green) — takes the first character of whatever follows the
    colon. Returns (code, display_text) with the signal line stripped out
    of display_text so it isn't shown twice.
    """
    code = "n"
    cleaned_lines = []
    for line in text.strip().split("\n"):
        stripped = line.strip().strip("*").strip()
        if stripped.upper().startswith("SIGNAL:"):
            raw = stripped.split(":", 1)[1].strip().lower()
            if raw and raw[0] in SIGNAL_LEVELS:
                code = raw[0]
            continue  # drop this line from what gets displayed/logged
        cleaned_lines.append(line)
    return code, "\n".join(cleaned_lines).strip()


# ── Utilities ─────────────────────────────────────────────

def hr(char="─", width=50):
    print(char * width)

def today():
    return datetime.date.today().strftime("%Y-%m-%d")

def prompt(label, allow_blank=True):
    """Prompt for input. Returns stripped string or empty string."""
    try:
        val = input(f"  {label}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nAborted.")
        sys.exit(0)
    return val

def ask_signal():
    """Ask for signal level, return (code, label, description)."""
    print()
    print("  Signal level:")
    for code, (label, desc) in SIGNAL_LEVELS.items():
        print(f"    [{code}] {label:8s} — {desc}")
    while True:
        choice = prompt("Your signal (g/y/r/n)").lower()
        if choice in SIGNAL_LEVELS:
            return choice, *SIGNAL_LEVELS[choice]
        print("  Enter g, y, r, or n.")


# ── Weekly scan ───────────────────────────────────────────

def run_weekly_scan():
    hr("═")
    print("  SNKF PROTOCOL — Weekly Ecosystem Scan (v0.2 — AI-assisted)")
    print(f"  {today()}")
    hr("═")

    shell = ClaudeShell(system_prompt=SCAN_SYSTEM_PROMPT)
    results = []
    all_citations = []
    overall_signal = "n"
    signal_priority = ["n", "g", "y", "r"]  # highest index wins

    # signal_log is a wrap-up, not a search target — handled separately below
    scan_checkpoints = [cp for cp in WEEKLY_CHECKPOINTS if cp["id"] != "signal_log"]

    for i, cp in enumerate(scan_checkpoints, 1):
        print()
        hr()
        print(f"  [{i}/{len(scan_checkpoints)}] {cp['label']}")
        print(f"  ↳ {cp['hint']}")
        hr()
        print("  Searching...")

        query = build_query(cp)
        summary, citations, error = shell.ask_with_search(query)

        if error:
            # Degrade gracefully — fall back to v0.1's manual entry for
            # just this source rather than aborting the whole scan.
            print(f"  [Search failed: {error}]")
            note = prompt("Falling back to manual entry. What did you find? (Enter to skip)")
            if not note:
                results.append({"checkpoint": cp["label"], "note": "(skipped)", "signal": "n"})
                continue
            code, label, desc = ask_signal()
            results.append({"checkpoint": cp["label"], "note": note, "signal": label})
            if signal_priority.index(code) > signal_priority.index(overall_signal):
                overall_signal = code
            continue

        code, display_text = parse_signal(summary)
        signal_label, signal_desc = SIGNAL_LEVELS[code]

        print()
        print(f"  {display_text}")
        if citations:
            print()
            print("  Sources:")
            for c in citations[:5]:
                print(f"    - {c['title']}: {c['url']}")

        print()
        print(f"  AI-suggested signal: {signal_label.upper()} — {signal_desc}")
        override = prompt("Accept? (Enter to accept, or type g/y/r/n to override)").lower()
        final_code = override if override in SIGNAL_LEVELS else code
        final_label = SIGNAL_LEVELS[final_code][0]

        extra = prompt("Anything to add? (Enter to skip)")
        full_note = display_text if not extra else f"{display_text}\n    Your note: {extra}"

        results.append({"checkpoint": cp["label"], "note": full_note, "signal": final_label})
        all_citations.extend(citations)

        if signal_priority.index(final_code) > signal_priority.index(overall_signal):
            overall_signal = final_code

    # Signal log wrap-up — synthesized from what got flagged above,
    # since you're no longer manually reading every source yourself.
    flagged = [r for r in results if r["signal"] != "none"]
    print()
    hr()
    print(f"  Signal log — {len(flagged)} source(s) flagged this week")
    hr()
    for r in flagged:
        print(f"    [{r['signal']}] {r['checkpoint']}")
    wrap_note = prompt("Anything else to log for this week? (Enter to skip)")
    results.append({
        "checkpoint": "Signal log",
        "note": wrap_note or f"{len(flagged)} source(s) flagged this week",
        "signal": "none",
    })

    _print_scan_log(results, overall_signal, all_citations)


def _print_scan_log(results, overall_signal, all_citations=None):
    signal_label, signal_desc = SIGNAL_LEVELS[overall_signal]

    # Compress non-empty notes into a scan note string
    flagged = [r for r in results if r["note"] != "(skipped)" and r["signal"] != "none"]
    scan_note_parts = [r["note"][:60].replace("\n", " ") for r in flagged[:3]]  # cap at 3 for dashboard field
    scan_note = " · ".join(scan_note_parts) if scan_note_parts else "No flags this week"

    print()
    hr("═")
    print("  DASHBOARD LOG ENTRY — copy and paste into AaE_Dashboard.html")
    hr("═")
    print(f"  Category  : Scan (AI-assisted)")
    print(f"  Signal    : {signal_label.upper()} — {signal_desc}")
    print(f"  Scan note : {scan_note}")
    print(f"  Minutes   : 20")
    print()
    print("  Full notes:")
    for r in results:
        if r["note"] != "(skipped)":
            print(f"    [{r['signal']:8s}] {r['checkpoint']}: {r['note']}")
    if all_citations:
        # Dedup by url in case the same source got cited across checkpoints
        seen = set()
        unique = []
        for c in all_citations:
            if c["url"] not in seen:
                seen.add(c["url"])
                unique.append(c)
        print()
        print("  Sources cited this scan:")
        for c in unique:
            print(f"    - {c['title']}: {c['url']}")
    hr("═")
    print()


# ── Monthly review ────────────────────────────────────────

def run_monthly_review():
    hr("═")
    print("  SNKF PROTOCOL — Monthly Plan Review")
    print(f"  {today()}")
    hr("═")

    results = []
    changes = []

    for i, cp in enumerate(MONTHLY_CHECKPOINTS, 1):
        print()
        hr()
        print(f"  [{i}/{len(MONTHLY_CHECKPOINTS)}] {cp['label']}")
        print(f"  ↳ {cp['hint']}")
        hr()
        note = prompt("Notes (press Enter to skip)")
        changed = prompt("Did anything change? (y/n)").lower() == "y"
        results.append({"checkpoint": cp["label"], "note": note or "(no changes)", "changed": changed})
        if changed and note:
            changes.append(f"{cp['label']}: {note}")

    _print_review_log(results, changes)


def _print_review_log(results, changes):
    print()
    hr("═")
    print("  DASHBOARD LOG ENTRY — copy and paste into AaE_Dashboard.html")
    hr("═")
    print(f"  Category  : Review")
    print(f"  Signal    : {'YELLOW — discuss, maybe adjust' if changes else 'GREEN — noted, no changes'}")
    print(f"  Minutes   : 45")
    print()
    if changes:
        print("  Changes logged:")
        for c in changes:
            print(f"    • {c}")
    else:
        print("  No plan changes triggered.")
    print()
    print("  Full notes:")
    for r in results:
        status = "CHANGED" if r["changed"] else "stable"
        print(f"    [{status:8s}] {r['checkpoint']}: {r['note']}")
    hr("═")
    print()


# ── Entry point ───────────────────────────────────────────

def main():
    args = [a.lower() for a in sys.argv[1:]]

    if "--scan" in args:
        mode = "scan"
    elif "--review" in args:
        mode = "review"
    else:
        print()
        hr("═")
        print("  SNKF Protocol Runner v0.2")
        hr("═")
        print()
        print("  [1] Weekly Ecosystem Scan  (~20 min)")
        print("  [2] Monthly Plan Review    (~45 min)")
        print()
        choice = prompt("Choose (1 or 2)").strip()
        mode = "scan" if choice == "1" else "review" if choice == "2" else None
        if not mode:
            print("  Invalid choice. Run with --scan or --review to skip this prompt.")
            sys.exit(1)

    if mode == "scan":
        run_weekly_scan()
    elif mode == "review":
        run_monthly_review()


if __name__ == "__main__":
    main()
