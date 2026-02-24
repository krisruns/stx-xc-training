#!/usr/bin/env python3
"""
Generate Training Overview HTML from Training_Master CSV
St. Xavier Tigers — Hunter Green & Gold color scheme

Column order: Week | Start Date | Meet | Workout 1 | Workout 2 | Workout 3 ...

Rules:
- Workouts grouped BY DAY — same day V and JV entries go in the same cell, stacked
- Any non-easy, non-rest, non-blank value is a workout (including LR, LR-Progression)
- If V and JV have the same workout on a day: show once, no label
- If they differ: show both stacked with [V] and [JV] badges in one workout slot
- If only one squad has a workout on a given day: badge it if the other squad
  has any workouts this week; otherwise no badge needed
"""

import csv
from datetime import datetime

INPUT_CSV = "/mnt/user-data/uploads/Training_Master_-_Training_Overview.csv"
OUTPUT_HTML = "/mnt/user-data/outputs/training_overview.html"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def is_workout(val):
    """True if cell is a real workout (not easy / rest / blank)."""
    if not val or not val.strip():
        return False
    return val.strip().lower() not in {"easy", "rest"}

def load_weeks(filepath):
    weeks = {}
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            level = row.get("", "").strip()
            week_str = row.get("Week", "").strip()
            if not week_str:
                continue
            wk = int(week_str)
            if wk not in weeks:
                weeks[wk] = {"V": None, "JV": None}
            if level in ("V", "JV"):
                weeks[wk][level] = row
    return weeks

def extract_workouts(weeks):
    results = []
    for wk in sorted(weeks.keys()):
        vrow = weeks[wk]["V"]
        jvrow = weeks[wk]["JV"]
        if vrow is None:
            continue

        date_str = vrow.get("Beginning Date", "").strip()

        meet = (vrow.get("Meet") or "").strip()
        if jvrow:
            jv_meet = (jvrow.get("Meet") or "").strip()
            if jv_meet and jv_meet not in meet:
                meet = jv_meet if not meet else f"{meet} / {jv_meet}"

        jv_has_any = jvrow is not None and any(is_workout(jvrow.get(d) or "") for d in DAYS)
        v_has_any  = any(is_workout(vrow.get(d) or "") for d in DAYS)

        workout_slots = []
        for day in DAYS:
            v_val  = (vrow.get(day) or "").strip()
            jv_val = (jvrow.get(day) or "").strip() if jvrow else ""

            v_is  = is_workout(v_val)
            jv_is = is_workout(jv_val)

            if not v_is and not jv_is:
                continue

            if v_is and jv_is:
                if v_val.lower() == jv_val.lower():
                    workout_slots.append(v_val)
                else:
                    workout_slots.append(
                        f"<span class='wo-line'>{v_val} <span class='tag v-tag'>V</span></span>"
                        f"<span class='wo-line'>{jv_val} <span class='tag jv-tag'>JV</span></span>"
                    )
            elif v_is:
                label = f" <span class='tag v-tag'>V</span>" if jv_has_any else ""
                workout_slots.append(f"{v_val}{label}")
            else:
                label = f" <span class='tag jv-tag'>JV</span>" if v_has_any else ""
                workout_slots.append(f"{jv_val}{label}")

        results.append({
            "week": wk,
            "date": date_str,
            "meet": meet,
            "workouts": workout_slots,
        })
    return results


def generate_html(weeks_data):
    weeks_data = [w for w in weeks_data if w["workouts"] or w["meet"]]
    max_wo = 3

    def wo_cell(val):
        if not val:
            return '<td class="empty">—</td>'
        return f'<td class="workout-cell">{val}</td>'

    rows_html = ""
    for w in weeks_data:
        wo_cells = "".join(wo_cell(w["workouts"][i] if i < len(w["workouts"]) else "") for i in range(max_wo))
        meet_td = f'<td class="meet-cell">{w["meet"]}</td>' if w["meet"] else '<td class="empty">—</td>'
        rows_html += f"""
        <tr>
          <td class="week-num">Wk {w["week"]}</td>
          <td class="date-cell">{w["date"]}</td>
          {meet_td}
          {wo_cells}
        </tr>"""

    wo_headers = "".join(f"<th>Workout {i+1}</th>" for i in range(max_wo))
    now = datetime.now().strftime("%-m/%-d/%Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>STX Tigers · Track 2025-26 Training Overview</title>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --green-deep:   #0c1f13;
      --green-dark:   #122b18;
      --green-mid:    #1a3d22;
      --green-accent: #2a6b3a;
      --gold:         #c8972a;
      --gold-light:   #e8b84b;
      --gold-pale:    #f5dfa0;
      --silver:       #8daa93;
      --line:         rgba(80,160,100,0.18);
      --text:         #e4efe6;
      --text-dim:     #5e8c68;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: var(--green-deep);
      color: var(--text);
      font-family: 'Barlow', sans-serif;
      font-weight: 300;
      min-height: 100vh;
    }}

    /* ── HEADER ── */
    header {{
      background: linear-gradient(120deg, #09160d 0%, var(--green-dark) 55%, #152e1a 100%);
      border-bottom: 4px solid var(--gold);
      padding: 26px 40px 20px;
      display: flex;
      align-items: center;
      gap: 0;
      position: relative;
      overflow: hidden;
    }}

    /* decorative diagonal stripe */
    header::before {{
      content: '';
      position: absolute;
      right: -30px; top: -20px;
      width: 180px; height: 180px;
      background: rgba(200, 151, 42, 0.07);
      transform: rotate(30deg);
      pointer-events: none;
    }}

    .header-badge {{
      background: var(--gold);
      color: var(--green-deep);
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.65rem;
      font-weight: 900;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      padding: 3px 10px;
      border-radius: 2px;
      margin-right: 18px;
      white-space: nowrap;
    }}

    .header-text h1 {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 2.2rem;
      font-weight: 900;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #fff;
      line-height: 1.1;
    }}

    .header-text h1 em {{
      font-style: normal;
      color: var(--gold-light);
    }}

    .header-text p {{
      font-size: 0.78rem;
      color: var(--silver);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-top: 3px;
    }}

    /* ── CONTAINER ── */
    .container {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 28px 24px 60px;
    }}

    /* ── LEGEND ── */
    .legend {{
      display: flex;
      gap: 16px;
      margin-bottom: 18px;
      align-items: center;
    }}

    .legend-label {{
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--text-dim);
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.78rem;
      color: var(--silver);
    }}

    /* ── TAGS ── */
    .tag {{
      display: inline-block;
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.6rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      padding: 1px 5px;
      border-radius: 2px;
      vertical-align: middle;
      text-transform: uppercase;
      white-space: nowrap;
    }}

    .v-tag  {{ background: var(--gold); color: var(--green-deep); }}
    .jv-tag {{ background: #1c4a26; color: #82e89a; border: 1px solid #2e7a3a; }}

    /* ── TABLE ── */
    .table-wrap {{
      overflow-x: auto;
      border-radius: 6px;
      border: 1px solid var(--line);
      box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }}

    thead tr {{
      background: var(--green-mid);
      border-bottom: 2px solid var(--gold);
    }}

    thead th {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--gold-light);
      padding: 11px 14px;
      text-align: left;
      white-space: nowrap;
    }}

    /* Meet column header gets gold accent */
    thead th:nth-child(3) {{
      color: var(--gold-pale);
    }}

    tbody tr {{
      border-bottom: 1px solid var(--line);
      background: var(--green-dark);
      transition: background 0.12s;
    }}

    tbody tr:nth-child(even) {{
      background: rgba(9, 20, 11, 0.7);
    }}

    tbody tr:hover {{
      background: rgba(42, 107, 58, 0.18);
    }}

    td {{
      padding: 11px 14px;
      vertical-align: top;
      line-height: 1.55;
    }}

    .week-num {{
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 800;
      font-size: 0.92rem;
      color: var(--gold-light);
      white-space: nowrap;
      min-width: 52px;
    }}

    .date-cell {{
      color: var(--silver);
      font-size: 0.80rem;
      white-space: nowrap;
      min-width: 50px;
    }}

    .meet-cell {{
      color: var(--gold-pale);
      font-weight: 500;
      min-width: 120px;
      font-size: 0.83rem;
    }}

    .workout-cell {{
      min-width: 175px;
      max-width: 265px;
      color: var(--text);
    }}

    /* Stacked V / JV within one cell */
    .wo-line {{
      display: block;
      padding-bottom: 6px;
      margin-bottom: 6px;
      border-bottom: 1px solid var(--line);
    }}

    .wo-line:last-child {{
      padding-bottom: 0;
      margin-bottom: 0;
      border-bottom: none;
    }}

    .empty {{
      color: var(--text-dim);
      font-size: 0.75rem;
    }}

    .generated {{
      text-align: right;
      margin-top: 16px;
      font-size: 0.68rem;
      color: var(--text-dim);
      letter-spacing: 0.07em;
    }}
  </style>
</head>
<body>

<header>
  <div class="header-badge">Tigers</div>
  <div class="header-text">
    <h1>St. Xavier <em>Track 2025–26</em></h1>
    <p>Training Overview · Indoor &amp; Outdoor Season</p>
  </div>
</header>

<div class="container">
  <div class="legend">
    <span class="legend-label">Key:</span>
    <span class="legend-item"><span class="tag v-tag">V</span> Varsity</span>
    <span class="legend-item"><span class="tag jv-tag">JV</span> JV</span>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Week</th>
          <th>Start</th>
          <th>Meet</th>
          {wo_headers}
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
  </div>

  <p class="generated">Generated {now}</p>
</div>

</body>
</html>"""


def main():
    print("Loading CSV...")
    weeks = load_weeks(INPUT_CSV)
    print(f"Found {len(weeks)} weeks.")
    data = extract_workouts(weeks)
    html = generate_html(data)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
