#!/usr/bin/env python3
"""
STX Season Archive Generator
Usage: python generate_archive.py --start 1 --end 23 --season "XC 2025" --input ./weeks --output ./
"""

import argparse
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag


# ─── PARSER ───────────────────────────────────────────────────────────────────

def clean_text(element):
    """Strip tags, collapse whitespace, remove link text."""
    if element is None:
        return ""
    # Remove <a> tags entirely (links to mobility/warmup pages)
    for a in element.find_all("a"):
        a.decompose()
    text = element.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_week_xc(soup, week_num):
    """
    Parse XC-style week files (Weeks 1–23).
    Structure: div.day-section > div.groups-container > div.group
    """
    week = {"number": week_num, "dates": "", "days": [], "totals": {}, "notes": []}

    # Header dates
    header = soup.find("div", class_="week-dates") or soup.find("div", class_="header")
    if header:
        week["dates"] = clean_text(header)

    # Fall back: find dates in h1/h2/p near top
    if not week["dates"]:
        for tag in soup.find_all(["h1", "h2", "p"])[:5]:
            txt = clean_text(tag)
            if re.search(r"(june|july|august|september|october|november)", txt, re.I):
                week["dates"] = txt
                break

    # Days
    for day_div in soup.find_all("div", class_="day-section"):
        day = {}
        title_el = day_div.find("div", class_="day-title")
        day["title"] = clean_text(title_el) if title_el else ""

        groups = []
        for group_div in day_div.find_all("div", class_="group"):
            group = {}
            name_el = group_div.find("div", class_="group-name")
            group["name"] = clean_text(name_el) if name_el else "All Groups"

            sections = {}
            for ws in group_div.find_all("div", class_="workout-section"):
                label_el = ws.find("div", class_="workout-label")
                label = clean_text(label_el).rstrip(":") if label_el else ""
                content_el = ws.find("div", class_="workout-content")
                if content_el:
                    # Grab workout-main and workout-details separately
                    main_el = content_el.find("div", class_="workout-main")
                    detail_el = content_el.find("div", class_="workout-details")
                    parts = []
                    if main_el:
                        t = clean_text(main_el)
                        if t:
                            parts.append(t)
                    if detail_el:
                        t = clean_text(detail_el)
                        if t:
                            parts.append(t)
                    sections[label] = " — ".join(parts) if parts else ""
                else:
                    sections[label] = ""

            group["sections"] = sections
            groups.append(group)

        day["groups"] = groups
        if day["title"] or groups:
            week["days"].append(day)

    # Weekly mileage totals
    totals_div = soup.find("div", class_="totals-section")
    if totals_div:
        for item in totals_div.find_all("div", class_="total-item"):
            grp_el = item.find("div", class_="total-group")
            mi_el = item.find("div", class_="total-miles")
            if grp_el and mi_el:
                week["totals"][clean_text(grp_el)] = clean_text(mi_el)

    # Training notes
    notes_div = soup.find("div", class_="notes-section")
    if notes_div:
        for li in notes_div.find_all("li"):
            week["notes"].append(clean_text(li))

    return week


def parse_week_track(soup, week_num):
    """
    Parse track-style week files (Weeks 25+).
    Structure: div.day > div.day-content > div.workout-item[data-group]
    """
    week = {"number": week_num, "dates": "", "days": [], "totals": {}, "notes": []}

    header = soup.find("div", class_="header") or soup.find("h1")
    if header:
        week["dates"] = clean_text(header)

    for day_div in soup.find_all("div", class_="day"):
        day = {}
        header_el = day_div.find("div", class_="day-header")
        day["title"] = clean_text(header_el) if header_el else ""

        # Collect workout-items grouped by group name
        group_map = {}
        for item in day_div.find_all("div", class_="workout-item"):
            grp = item.get("data-group", "All Groups")
            desc_el = item.find("div", class_="workout-desc")
            miles_el = item.find("div", class_="workout-miles")
            parts = []
            if desc_el:
                parts.append(clean_text(desc_el))
            if miles_el:
                parts.append(clean_text(miles_el))
            entry = " ".join(parts)
            group_map.setdefault(grp, []).append(entry)

        groups = []
        for grp, entries in group_map.items():
            groups.append({
                "name": grp,
                "sections": {"RUN": "; ".join(entries)}
            })

        day["groups"] = groups
        if day["title"] or groups:
            week["days"].append(day)

    # Totals — track pages use div.totals > div.total > div.total-label + div.total-miles
    # Also handle XC-style div.totals-section as fallback
    totals_div = soup.find("div", class_="totals") or \
                 soup.find("div", class_=re.compile(r"totals-section|mileage-summary", re.I))
    if totals_div:
        for item in totals_div.find_all("div", class_="total"):
            grp_el = item.find("div", class_="total-label") or \
                     item.find("div", class_=re.compile(r"total-group|group-name", re.I))
            mi_el = item.find("div", class_="total-miles")
            if grp_el and mi_el:
                raw = clean_text(mi_el)
                # Bare number (e.g. "42") — append "miles" for display consistency
                val = f"{raw} miles" if raw.replace(".", "").isdigit() else raw
                week["totals"][clean_text(grp_el)] = val

    # If still empty, compute by summing workout-miles across all days per group
    if not week["totals"]:
        group_miles = {}
        for item in soup.find_all("div", class_="workout-item"):
            grp = item.get("data-group", "").strip()
            if not grp:
                continue
            miles_el = item.find("div", class_="workout-miles")
            if miles_el:
                # Parse numeric value from strings like "4.0 mi" or "4 miles"
                raw = clean_text(miles_el)
                m = re.search(r"(\d+\.?\d*)", raw)
                if m:
                    group_miles[grp] = group_miles.get(grp, 0.0) + float(m.group(1))
        for grp, total in group_miles.items():
            # Format: whole number if clean, one decimal if needed
            formatted = f"{int(total)} miles" if total == int(total) else f"{total:.1f} miles"
            week["totals"][grp] = formatted

    notes_div = soup.find("div", class_="notes-section")
    if notes_div:
        for li in notes_div.find_all("li"):
            week["notes"].append(clean_text(li))

    return week


def extract_short_date(date_str):
    """Pull a compact date like 'June 2' or 'Nov 1' from a longer date string."""
    # Try to find patterns like "June 2" or "November 1, 2025"
    m = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"[\s.]+(\d{1,2})",
        date_str, re.I
    )
    if m:
        month = m.group(1).capitalize()
        # Abbreviate months longer than 4 chars
        abbrevs = {"January":"Jan","February":"Feb","March":"Mar","April":"Apr",
                   "August":"Aug","September":"Sep","October":"Oct",
                   "November":"Nov","December":"Dec"}
        month = abbrevs.get(month, month)
        return f"{month} {m.group(2)}"
    return date_str


def build_date_range(weeks):
    """Auto-detect season date range from first and last week's date strings."""
    first_date = next((w["dates"] for w in weeks if w["dates"]), "")
    last_date = next((w["dates"] for w in reversed(weeks) if w["dates"]), "")

    start = extract_short_date(first_date)
    end_str = last_date
    # For last week, grab the END of its range (e.g. "Aug 18 - Aug 24" → "Aug 24")
    dash_split = re.split(r"\s*[–—-]\s*", last_date)
    if len(dash_split) >= 2:
        end_str = dash_split[-1].strip()
    end = extract_short_date(end_str)

    if start and end and start != end:
        return f"{start} – {end}"
    return start or ""


def detect_structure(soup):
    """Return 'xc' or 'track' based on HTML structure."""
    if soup.find("div", class_="day-section"):
        return "xc"
    if soup.find("div", class_="workout-item"):
        return "track"
    return "xc"  # default


def parse_week_file(filepath, week_num, debug=False):
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    structure = detect_structure(soup)
    if debug:
        print(f"      structure detected: {structure}")
        totals_div = soup.find("div", class_="totals") or soup.find("div", class_="totals-section")
        if totals_div:
            print(f"      totals container found: class='{totals_div.get('class')}'")
            items = totals_div.find_all("div", class_="total")
            print(f"      total items found: {len(items)}")
            for item in items:
                lbl = item.find("div", class_="total-label")
                mi  = item.find("div", class_="total-miles")
                print(f"        → label='{clean_text(lbl) if lbl else None}'  miles='{clean_text(mi) if mi else None}'")
        else:
            print(f"      ⚠️  no totals container found (tried div.totals and div.totals-section)")
    if structure == "track":
        return parse_week_track(soup, week_num)
    else:
        return parse_week_xc(soup, week_num)


# ─── HTML GENERATION ──────────────────────────────────────────────────────────

GROUP_COLORS = {
    "GOLD": "#b8860b",
    "GREEN": "#2d6a2d",
    "WHITE": "#555",
    "FRESHMAN": "#8b4513",
    "FR": "#8b4513",
    "ALL GROUPS": "#333",
}

def group_color(name):
    return GROUP_COLORS.get(name.upper(), "#444")


def render_day_table(day):
    """Render one day as a compact table row block."""
    if not day["groups"]:
        return ""
    
    title = day["title"] or "—"
    rows = ""
    for g in day["groups"]:
        color = group_color(g["name"])
        secs = g.get("sections", {})
        # For XC files show PRE/RUN/POST; for track just RUN
        cells = ""
        for label in ["PRE", "RUN", "POST"]:
            val = secs.get(label, "")
            cells += f'<td class="cell">{val}</td>'
        if not any(secs.get(l) for l in ["PRE", "RUN", "POST"]):
            # Maybe only has RUN from track parser
            run_val = secs.get("RUN", "")
            cells = f'<td class="cell" colspan="3">{run_val}</td>'
        
        rows += f'''
        <tr>
          <td class="group-cell" style="color:{color};font-weight:600">{g["name"]}</td>
          {cells}
        </tr>'''

    return f'''
    <div class="day-block">
      <div class="day-label">{title}</div>
      <table class="day-table">
        <thead><tr>
          <th class="group-hdr">Group</th>
          <th>Pre</th><th>Run</th><th>Post</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''


def render_totals(totals):
    if not totals:
        return ""
    chips = "".join(
        f'<span class="chip" style="border-color:{group_color(g)};color:{group_color(g)}">'
        f'<strong>{g}</strong> {m}</span>'
        for g, m in totals.items()
    )
    return f'<div class="totals-row">{chips}</div>'


def render_notes(notes):
    if not notes:
        return ""
    items = "".join(f"<li>{n}</li>" for n in notes)
    return f'<div class="notes-block"><strong>Training Notes</strong><ul>{items}</ul></div>'


def render_week_interactive(week):
    """Collapsible week card for the interactive version."""
    week_id = f"week-{week['number']}"
    days_html = "".join(render_day_table(d) for d in week["days"])
    totals_html = render_totals(week["totals"])
    notes_html = render_notes(week["notes"])
    dates = week["dates"] or ""

    total_chips = ""
    if week["totals"]:
        chips = " ".join(
            f'<span class="mileage-chip" style="color:{group_color(g)}">{g} {m}</span>'
            for g, m in week["totals"].items()
        )
        total_chips = f'&nbsp;&nbsp;{chips}'

    return f'''
<div class="week-card" id="{week_id}">
  <div class="week-header" onclick="toggle('{week_id}')">
    <span class="week-title">Week {week["number"]}</span>
    <span class="week-meta"><span class="date-range">{dates}</span>{total_chips}</span>
    <span class="caret">▼</span>
  </div>
  <div class="week-body" id="body-{week_id}">
    {totals_html}
    {days_html}
    {notes_html}
  </div>
</div>'''


def render_week_print(week):
    """Print-optimized week section (no JS, no collapse)."""
    days_html = "".join(render_day_table(d) for d in week["days"])
    totals_html = render_totals(week["totals"])
    notes_html = render_notes(week["notes"])
    dates = week["dates"] or ""

    return f'''
<div class="print-week">
  <div class="print-week-header">
    <span class="week-title">Week {week["number"]}</span>
    <span class="week-meta">{dates}</span>
  </div>
  {totals_html}
  {days_html}
  {notes_html}
</div>'''


SHARED_CSS = """
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 0; padding: 20px; background: #f4f4f4; color: #222; font-size: 13px; }
  h1 { text-align: center; color: #1a1a2e; margin-bottom: 4px; }
  .subtitle { text-align: center; color: #666; margin-bottom: 24px; font-size: 0.9rem; }
  .week-card { background: #fff; border-radius: 8px; margin-bottom: 10px;
               box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: hidden; }
  .week-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px;
                 cursor: pointer; background: #3a5f8a; color: #fff; }
  .week-header:hover { background: #2e4f77; }
  .week-title { font-size: 1rem; font-weight: 700; min-width: 80px; }
  .week-meta { flex: 1; font-size: 0.8rem; }
  .week-meta .date-range { opacity: 0.9; margin-right: 8px; }
  .mileage-chip { font-weight: 700; font-size: 0.78rem;
                  background: rgba(255,255,255,0.18); border-radius: 4px;
                  padding: 1px 6px; margin-left: 4px; }
  .caret { font-size: 0.75rem; transition: transform .2s; }
  .week-body { padding: 12px 16px; display: none; }
  .week-body.open { display: block; }
  .day-block { margin-bottom: 14px; }
  .day-label { font-weight: 700; font-size: 0.85rem; color: #444; text-transform: uppercase;
               border-bottom: 1px solid #eee; padding-bottom: 4px; margin-bottom: 6px; }
  .day-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  .day-table th { background: #f0f0f0; padding: 4px 8px; text-align: left;
                  font-size: 0.75rem; color: #666; text-transform: uppercase; }
  .group-hdr { width: 90px; }
  .group-cell { width: 90px; padding: 5px 8px; vertical-align: top; white-space: nowrap; }
  .cell { padding: 5px 8px; vertical-align: top; border-left: 1px solid #f0f0f0; }
  .day-table tr:nth-child(even) { background: #fafafa; }
  .totals-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .chip { border: 1.5px solid; border-radius: 20px; padding: 3px 10px;
          font-size: 0.78rem; background: #fff; }
  .notes-block { background: #fffbea; border-left: 3px solid #f0c040;
                 padding: 10px 14px; border-radius: 4px; margin-top: 12px; font-size: 0.82rem; }
  .notes-block ul { margin: 6px 0 0 16px; padding: 0; }
  .notes-block li { margin-bottom: 4px; }
"""

PRINT_EXTRA_CSS = """
  @media print {
    body { background: white; padding: 10px; font-size: 11px; }
    .print-week { page-break-inside: avoid; margin-bottom: 20px; }
    .print-week-header { background: #3a5f8a !important; color: white !important;
                         -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
  .print-week { background: #fff; border-radius: 6px; margin-bottom: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,.1); overflow: hidden; }
  .print-week-header { display: flex; align-items: center; gap: 12px; padding: 10px 14px;
                       background: #3a5f8a; color: #fff; }
  .print-week-header .week-title { font-size: 1rem; font-weight: 700; min-width: 80px; }
  .print-week-header .week-meta { flex: 1; font-size: 0.8rem; opacity: 0.85; }
  .print-week .week-body, .print-week > .totals-row,
  .print-week > .day-block, .print-week > .notes-block { padding: 10px 14px; }
"""


def build_interactive(weeks, season_name, date_range):
    cards = "\n".join(render_week_interactive(w) for w in weeks)
    heading = f"{season_name} · {date_range}" if date_range else season_name
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{heading} — Archive</title>
<style>
{SHARED_CSS}
</style>
</head>
<body>
<h1>🏃 {heading}</h1>
<p class="subtitle">Season Archive &nbsp;·&nbsp; {len(weeks)} weeks &nbsp;·&nbsp;
  <a href="#" onclick="expandAll()">Expand All</a> &nbsp;|&nbsp;
  <a href="#" onclick="collapseAll()">Collapse All</a>
</p>
{cards}
<script>
function toggle(id) {{
  const body = document.getElementById('body-' + id);
  const card = document.getElementById(id);
  const caret = card.querySelector('.caret');
  body.classList.toggle('open');
  caret.style.transform = body.classList.contains('open') ? 'rotate(180deg)' : '';
}}
function expandAll() {{
  document.querySelectorAll('.week-body').forEach(b => b.classList.add('open'));
  document.querySelectorAll('.caret').forEach(c => c.style.transform = 'rotate(180deg)');
}}
function collapseAll() {{
  document.querySelectorAll('.week-body').forEach(b => b.classList.remove('open'));
  document.querySelectorAll('.caret').forEach(c => c.style.transform = '');
}}
</script>
</body>
</html>"""


def build_print(weeks, season_name, date_range):
    sections = "\n".join(render_week_print(w) for w in weeks)
    heading = f"{season_name} · {date_range}" if date_range else season_name
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{heading} — Print Archive</title>
<style>
{SHARED_CSS}
{PRINT_EXTRA_CSS}
</style>
</head>
<body>
<h1>🏃 {heading}</h1>
<p class="subtitle">Season Archive &nbsp;·&nbsp; {len(weeks)} weeks &nbsp;·&nbsp; Print / Save as PDF</p>
<button onclick="window.print()" style="display:block;margin:0 auto 20px;padding:8px 24px;
  background:#3a5f8a;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.9rem;">
  🖨 Print / Save PDF
</button>
{sections}
</body>
</html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a condensed season archive from week HTML files.")
    parser.add_argument("--start", type=int, required=True, help="First week number")
    parser.add_argument("--end", type=int, required=True, help="Last week number")
    parser.add_argument("--season", type=str, default="STX Season Archive", help='Season label, e.g. "XC 2025"')
    parser.add_argument("--input", type=str, default=".", help="Directory containing weekNN.html files")
    parser.add_argument("--output", type=str, default=".", help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Print parser diagnostics for each file")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    weeks = []
    missing = []
    for n in range(args.start, args.end + 1):
        filepath = input_dir / f"week{n:02d}.html"
        if not filepath.exists():
            filepath = input_dir / f"week{n}.html"
        if not filepath.exists():
            missing.append(n)
            print(f"  ⚠️  week{n:02d}.html not found — skipping")
            continue
        print(f"  ✓  Parsing week {n} ({filepath.name})")
        weeks.append(parse_week_file(filepath, n, debug=args.debug))

    if not weeks:
        print("No week files found. Check --input path.")
        return

    date_range = build_date_range(weeks)
    if date_range:
        print(f"   Date range detected: {date_range}")

    # Filename slug: season + date range if available
    full_label = f"{args.season} {date_range}" if date_range else args.season
    slug = re.sub(r"[^a-z0-9]+", "-", full_label.lower()).strip("-")

    interactive_path = output_dir / f"{slug}-archive.html"
    print_path = output_dir / f"{slug}-archive-print.html"

    interactive_path.write_text(build_interactive(weeks, args.season, date_range), encoding="utf-8")
    print_path.write_text(build_print(weeks, args.season, date_range), encoding="utf-8")

    print(f"\n✅ Done — {len(weeks)} weeks processed ({len(missing)} skipped)")
    print(f"   Interactive: {interactive_path}")
    print(f"   Print/PDF:   {print_path}")


if __name__ == "__main__":
    main()
