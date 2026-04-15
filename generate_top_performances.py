#!/usr/bin/env python3
"""
STX Top Performances Generator
Generates an HTML report of top performances for 800m, 1600/Mile, and 3200/2Mile.
For 800m, the faster of an athlete's individual 800 or 4x800 relay split is used.
Relay splits are marked with a lowercase 'r' (e.g., 2:01.2r).

Usage:
    python generate_top_performances.py \
        --athletes Athlete_Groups - Data.csv \
        [--relays relay_splits.csv] \
        [--top 10] \
        [--output top_performances.html]

Relay splits CSV format (optional):
    Athlete,4x800_Split
    Nick Sanders,1:54.2
    Anthony Passafiume,1:57.8
    ...
"""

import argparse
import csv
import os
import sys
from datetime import datetime

# Directory containing this script — used for default file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Time utilities
# ---------------------------------------------------------------------------

def parse_time(time_str: str) -> float | None:
    """Convert a time string (m:ss.t or ss.t) to total seconds. Returns None if blank/invalid."""
    if not time_str or not time_str.strip():
        return None
    time_str = time_str.strip()
    try:
        if ":" in time_str:
            parts = time_str.split(":")
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(time_str)
    except (ValueError, IndexError):
        return None


def format_time(seconds: float) -> str:
    """Convert total seconds back to m:ss.t string, always keeping one decimal place."""
    minutes = int(seconds // 60)
    secs = seconds - minutes * 60
    # Round to 1 decimal to avoid floating point artifacts (e.g. 2:03.00000001)
    secs = round(secs, 1)
    if minutes > 0:
        return f"{minutes}:{secs:04.1f}"
    else:
        return f"{secs:.1f}"


def format_time_display(seconds: float, is_relay: bool = False) -> str:
    """Return formatted time string with optional relay indicator."""
    t = format_time(seconds)
    return f"{t}r" if is_relay else t


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

# Column indices matching the two-row header format:
#   Row 1: Athlete | Grad Year | Current Season (x5) | All Time (x5)
#   Row 2:         |           | 800M | 4x800 Split | 1600/Mile | 3200/2 Mile | 5000M | (same x5)
_CS_800M  = 2
_CS_4x800 = 3
_CS_1600  = 4
_CS_3200  = 5


def load_athletes(filepath: str) -> list[dict]:
    """
    Load athlete performances from the two-row-header CSV.
    Only Current Season columns are extracted.
    Returns a list of dicts with keys: Athlete, cs_800m, cs_4x800, cs_1600, cs_3200.
    """
    athletes = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Data starts at row index 2 (skip both header rows)
    for row in rows[2:]:
        if not row or not row[0].strip():
            continue
        def get(idx, r=row):
            return r[idx].strip() if idx < len(r) else ""
        athletes.append({
            "Athlete":  get(0),
            "cs_800m":  get(_CS_800M),
            "cs_4x800": get(_CS_4x800),
            "cs_1600":  get(_CS_1600),
            "cs_3200":  get(_CS_3200),
        })
    return athletes


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

def build_rankings(athletes: list[dict], top_n: int) -> dict:
    """
    Returns a dict keyed by event label with a list of top-N dicts:
        {rank, name, time_display, time_seconds}
    For 800m, the faster of cs_800m and cs_4x800 is used; relay split marked with 'r'.
    """
    rankings = {}

    events = {
        "800m":        ("cs_800m",  "cs_4x800"),
        "1600/Mile":   ("cs_1600",  None),
        "3200/2 Mile": ("cs_3200",  None),
    }

    for event_label, (col, relay_col) in events.items():
        entries = []

        for athlete in athletes:
            name = athlete.get("Athlete", "")
            ind_time   = parse_time(athlete.get(col, ""))
            relay_time = parse_time(athlete.get(relay_col, "")) if relay_col else None

            if relay_col:
                # Pick the faster of individual 800 and relay split
                if ind_time is not None and relay_time is not None:
                    if relay_time < ind_time:
                        entries.append({"name": name, "seconds": relay_time, "relay": True})
                    else:
                        entries.append({"name": name, "seconds": ind_time,   "relay": False})
                elif ind_time is not None:
                    entries.append({"name": name, "seconds": ind_time,   "relay": False})
                elif relay_time is not None:
                    entries.append({"name": name, "seconds": relay_time, "relay": True})
            else:
                if ind_time is not None:
                    entries.append({"name": name, "seconds": ind_time, "relay": False})

        # Sort fastest first
        entries.sort(key=lambda x: x["seconds"])

        # Assign ranks (handle ties)
        ranked = []
        prev_seconds = None
        prev_rank = 0
        for i, entry in enumerate(entries[:top_n]):
            if entry["seconds"] == prev_seconds:
                rank = prev_rank
            else:
                rank = i + 1
                prev_rank = rank
            prev_seconds = entry["seconds"]
            ranked.append({
                "rank":         rank,
                "name":         entry["name"],
                "time_display": format_time_display(entry["seconds"], entry["relay"]),
                "time_seconds": entry["seconds"],
            })

        rankings[event_label] = ranked

    return rankings


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>STX Top {top_n} Performances</title>
  <style>
    :root {{
      --gold:   #C9A84C;
      --black:  #1A1A1A;
      --white:  #FFFFFF;
      --gray:   #F4F4F4;
      --border: #D0D0D0;
      --accent: #8B0000;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: var(--gray);
      color: var(--black);
      padding: 2rem 1rem;
    }}

    header {{
      text-align: center;
      margin-bottom: 2.5rem;
    }}

    header h1 {{
      font-size: 2rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--black);
    }}

    header h1 span {{
      color: var(--gold);
    }}

    header p.subtitle {{
      color: #555;
      margin-top: 0.4rem;
      font-size: 0.9rem;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
      max-width: 1100px;
      margin: 0 auto;
    }}

    .card {{
      background: var(--white);
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }}

    .card-header {{
      background: var(--black);
      color: var(--white);
      padding: 0.85rem 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .card-header h2 {{
      font-size: 1.1rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      flex: 1;
    }}

    .card-header .badge {{
      background: var(--gold);
      color: var(--black);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 99px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
    }}

    thead tr {{
      background: var(--gray);
      border-bottom: 2px solid var(--border);
    }}

    thead th {{
      padding: 0.6rem 1rem;
      text-align: left;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #666;
    }}

    thead th.time-col {{ text-align: right; }}

    tbody tr {{
      border-bottom: 1px solid var(--border);
      transition: background 0.15s;
    }}

    tbody tr:last-child {{ border-bottom: none; }}
    tbody tr:hover {{ background: #faf7ee; }}

    /* Gold medal row */
    tbody tr.rank-1 {{
      background: #fffbee;
    }}
    tbody tr.rank-1 td.rank {{ color: var(--gold); font-weight: 800; }}

    td {{
      padding: 0.65rem 1rem;
      font-size: 0.92rem;
    }}

    td.rank {{
      width: 2.5rem;
      font-weight: 700;
      color: #999;
      font-size: 0.85rem;
    }}

    td.name {{ font-weight: 500; }}

    td.time {{
      text-align: right;
      font-family: 'Courier New', monospace;
      font-weight: 700;
      font-size: 0.95rem;
      color: var(--accent);
    }}

    td.time .relay-indicator {{
      font-size: 0.75rem;
      color: #888;
      font-style: italic;
    }}

    footer {{
      text-align: center;
      margin-top: 2.5rem;
      font-size: 0.8rem;
      color: #aaa;
    }}

    footer .note {{
      margin-top: 0.4rem;
      color: #bbb;
    }}
  </style>
</head>
<body>

<header>
  <h1>STX <span>Top {top_n}</span> Performances</h1>
  <p class="subtitle">Generated {date} &nbsp;|&nbsp; <em>r</em> = relay split</p>
</header>

<div class="grid">
{cards}
</div>

<footer>
  <div>Saint Xavier Cross Country 2025</div>
  <div class="note">* Relay splits (marked <em>r</em>) represent individual legs of the 4×800 relay.</div>
</footer>

</body>
</html>
"""

CARD_TEMPLATE = """  <div class="card">
    <div class="card-header">
      <h2>{event}</h2>
      <span class="badge">Top {top_n}</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Athlete</th>
          <th class="time-col">Time</th>
        </tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>"""

ROW_TEMPLATE = """        <tr class="{row_class}">
          <td class="rank">{rank}</td>
          <td class="name">{name}</td>
          <td class="time">{time}</td>
        </tr>"""


def build_time_cell(time_display: str) -> str:
    """Render time, highlighting the relay 'r' separately."""
    if time_display.endswith("r"):
        base = time_display[:-1]
        return f'{base}<span class="relay-indicator">r</span>'
    return time_display


def render_html(rankings: dict, top_n: int) -> str:
    cards_html = []
    for event, entries in rankings.items():
        rows = []
        for e in entries:
            row_class = f"rank-{e['rank']}" if e["rank"] <= 3 else ""
            rows.append(ROW_TEMPLATE.format(
                row_class=row_class,
                rank=e["rank"],
                name=e["name"],
                time=build_time_cell(e["time_display"]),
            ))
        cards_html.append(CARD_TEMPLATE.format(
            event=event,
            top_n=top_n,
            rows="\n".join(rows),
        ))

    return HTML_TEMPLATE.format(
        top_n=top_n,
        date=datetime.now().strftime("%B %d, %Y"),
        cards="\n".join(cards_html),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Generate STX top performances HTML report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--athletes", "-a",
        default=os.path.join(script_dir, "Athlete_Groups - Data.csv"),
        help="Path to athlete performances CSV (default: <script dir>/Athlete_Groups - Data.csv)",
    )
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(script_dir, "top_performances.html"),
        help="Output HTML file path (default: <script dir>/top_performances.html)",
    )

    args = parser.parse_args()

    # Validate CSV exists
    if not os.path.exists(args.athletes):
        print(f"ERROR: Athlete CSV not found: {args.athletes}", file=sys.stderr)
        sys.exit(1)

    # Load data first so we know the total athlete count
    print(f"Loading athletes from: {args.athletes}")
    athletes = load_athletes(args.athletes)
    print(f"  → {len(athletes)} athletes loaded")

    # Prompt for number of top performances
    total = len(athletes)
    while True:
        raw = input(f"\nHow many top performances to include? (1-{total} or A for all): ").strip()
        if raw.upper() == "A":
            top_n = total
            break
        try:
            top_n = int(raw)
            if 1 <= top_n <= total:
                break
            print(f"  Please enter a number between 1 and {total}, or A for all.")
        except ValueError:
            print(f"  Invalid input. Enter a number between 1 and {total}, or A for all.")

    # Build rankings
    label = "all" if top_n == total else f"top-{top_n}"
    print(f"\nBuilding {label} rankings...")
    rankings = build_rankings(athletes, top_n)
    for event, entries in rankings.items():
        print(f"  {event}: {len(entries)} entries")

    # Render HTML
    html = render_html(rankings, top_n)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✓ Report written to: {args.output}")


if __name__ == "__main__":
    main()
