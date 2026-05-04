"""
run_protocol.py — Sankofa Tools
SNKF Protocol Runner v0.1

Runs the weekly ecosystem scan or monthly plan review from the terminal.
Walks through each checkpoint interactively, collects your notes,
classifies signal, and prints a formatted dashboard log entry at the end.

Usage:
    python3 run_protocol.py          # prompts you to choose scan or review
    python3 run_protocol.py --scan   # weekly ecosystem scan
    python3 run_protocol.py --review # monthly plan review

v0.1 — no API calls, pure CLI workflow
v0.2 — AI-assist layer: signal classification suggestions via Claude Shell
"""

import sys
import datetime


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
    print("  SNKF PROTOCOL — Weekly Ecosystem Scan")
    print(f"  {today()}")
    hr("═")

    results = []
    overall_signal = "n"
    signal_priority = ["n", "g", "y", "r"]  # highest index wins

    for i, cp in enumerate(WEEKLY_CHECKPOINTS, 1):
        print()
        hr()
        print(f"  [{i}/{len(WEEKLY_CHECKPOINTS)}] {cp['label']}")
        print(f"  ↳ {cp['hint']}")
        hr()
        note = prompt("What did you find? (press Enter to skip)")
        if not note:
            results.append({"checkpoint": cp["label"], "note": "(skipped)", "signal": "n"})
            continue

        code, label, desc = ask_signal()
        results.append({"checkpoint": cp["label"], "note": note, "signal": label})

        # Track highest signal across all checkpoints
        if signal_priority.index(code) > signal_priority.index(overall_signal):
            overall_signal = code

    # Build dashboard log entry
    _print_scan_log(results, overall_signal)


def _print_scan_log(results, overall_signal):
    signal_label, signal_desc = SIGNAL_LEVELS[overall_signal]

    # Compress non-empty notes into a scan note string
    flagged = [r for r in results if r["note"] != "(skipped)" and r["signal"] != "none"]
    scan_note_parts = [r["note"][:60] for r in flagged[:3]]  # cap at 3 for dashboard field
    scan_note = " · ".join(scan_note_parts) if scan_note_parts else "No flags this week"

    print()
    hr("═")
    print("  DASHBOARD LOG ENTRY — copy and paste into AaE_Dashboard.html")
    hr("═")
    print(f"  Category  : Scan")
    print(f"  Signal    : {signal_label.upper()} — {signal_desc}")
    print(f"  Scan note : {scan_note}")
    print(f"  Minutes   : 20")
    print()
    print("  Full notes:")
    for r in results:
        if r["note"] != "(skipped)":
            print(f"    [{r['signal']:8s}] {r['checkpoint']}: {r['note']}")
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
        print("  SNKF Protocol Runner v0.1")
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
