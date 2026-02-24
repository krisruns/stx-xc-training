#!/usr/bin/env python3
"""
Convert weekly training CSV to filterable HTML (handles optional Racer/Non-Racer status)
Flexible version - works with "Racer"/"Racers" and "Non-Racer"/"Non-Racers"
Usage: python csv_to_html_flexible.py week25_schedule.csv
"""

import csv
from collections import defaultdict
import sys
import re

def normalize_status(status):
    """Normalize status values to handle both singular and plural forms"""
    if not status:
        return 'normal'
    status = status.strip()
    # Handle both Racer/Racers and Non-Racer/Non-Racers
    if 'non' in status.lower():
        return 'Non-Racer'
    elif status.lower() in ['racer', 'racers', 'racing']:
        return 'Racer'
    return 'normal'

def read_schedule(csv_file):
    """Read the CSV schedule file"""
    schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    totals = defaultdict(int)
    week_info = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            week = row['Week']
            day = row['Day']
            group = row['Group']
            status = row.get('Status', '').strip()
            
            week_info['week'] = week
            if row.get('Notes') and not week_info.get('phase'):
                week_info['phase'] = row['Notes']
            
            # Normalize status (handles Racer/Racers and Non-Racer/Non-Racers)
            status_key = normalize_status(status)
            
            schedule[day][status_key][group] = {
                'pre': row.get('Pre', ''),
                'main': row.get('Main_Workout', ''),
                'post': row.get('Post', ''),
                'miles': float(row.get('Miles', 0)) if row.get('Miles') else 0,
                'notes': row.get('Notes', '')
            }
            
            totals[group] += float(row.get('Miles', 0)) if row.get('Miles') else 0
    
    return schedule, totals, week_info

def generate_html(csv_file):
    """Generate filterable HTML from CSV"""
    
    schedule, totals, week_info = read_schedule(csv_file)
    
    phase = week_info.get('phase', 'Training Week')
    week_num = week_info['week']
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX Training Week {week_num}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 0 20px; background: #fafafa; }}
        h1 {{ color: #2c5530; border-bottom: 3px solid #4a7c59; padding-bottom: 10px; }}
        .subtitle {{ color: #666; margin-bottom: 20px; }}
        .totals {{ display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }}
        .total {{ padding: 15px 20px; background: white; border-radius: 6px; flex: 1; min-width: 140px; text-align: center; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .total:hover {{ transform: translateY(-2px); box-shadow: 0 2px 6px rgba(0,0,0,0.15); }}
        .total.gold {{ border-left: 4px solid #DAA520; }}
        .total.gold.active {{ background: #DAA520; color: white; }}
        .total.green {{ border-left: 4px solid #4a7c59; }}
        .total.green.active {{ background: #4a7c59; color: white; }}
        .total.white {{ border-left: 4px solid #888; }}
        .total.white.active {{ background: #888; color: white; }}
        .total.freshman {{ border-left: 4px solid #4169E1; }}
        .total.freshman.active {{ background: #4169E1; color: white; }}
        .total-label {{ font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }}
        .total-miles {{ font-size: 1.8rem; font-weight: 700; }}
        .filters {{ margin: 20px 0; text-align: center; }}
        .filter-btn {{ padding: 8px 16px; margin: 0 5px 5px 0; border: 2px solid #4a7c59; background: white; color: #4a7c59; border-radius: 4px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }}
        .filter-btn:hover, .filter-btn.active {{ background: #4a7c59; color: white; }}
        .day {{ margin: 25px 0; border-radius: 8px; overflow: hidden; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .day-header {{ background: linear-gradient(135deg, #2c5530 0%, #4a7c59 100%); padding: 15px 20px; color: white; font-size: 1.2rem; font-weight: 700; letter-spacing: 0.5px; }}
        .day-content {{ padding: 20px; }}
        .status-section {{ margin-bottom: 25px; }}
        .status-section:last-child {{ margin-bottom: 0; }}
        .status-title {{ font-size: 1.1rem; font-weight: 700; color: #2c5530; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }}
        .section {{ margin-bottom: 20px; }}
        .section:last-child {{ margin-bottom: 0; }}
        .section-label {{ font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #666; margin-bottom: 10px; letter-spacing: 0.5px; }}
        .workout-item {{ padding: 10px 15px; margin-bottom: 8px; border-radius: 4px; display: flex; align-items: center; gap: 12px; transition: all 0.2s; }}
        .workout-item:last-child {{ margin-bottom: 0; }}
        .workout-item.hidden {{ display: none; }}
        .workout-item.gold {{ background: #FFF9E6; border-left: 4px solid #DAA520; }}
        .workout-item.green {{ background: #F0F9F0; border-left: 4px solid #4a7c59; }}
        .workout-item.white {{ background: #F5F5F5; border-left: 4px solid #888; }}
        .workout-item.freshman {{ background: #E6F0FF; border-left: 4px solid #4169E1; }}
        .workout-item:hover {{ transform: translateX(5px); }}
        .group-badge {{ font-weight: 700; min-width: 80px; font-size: 0.9rem; text-transform: uppercase; }}
        .group-badge.gold {{ color: #B8860B; }}
        .group-badge.green {{ color: #2c5530; }}
        .group-badge.white {{ color: #555; }}
        .group-badge.freshman {{ color: #1E3A8A; }}
        .workout-desc {{ flex: 1; font-size: 0.95rem; }}
        .workout-miles {{ font-weight: 700; font-size: 1rem; white-space: nowrap; }}
        .pre-post {{ font-size: 0.9rem; color: #666; background: #f8f8f8; padding: 8px 15px; border-radius: 4px; font-style: italic; }}
        @media (max-width: 768px) {{
            .totals {{ flex-direction: column; }}
            .workout-item {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
            .workout-miles {{ align-self: flex-end; }}
        }}
    </style>
</head>
<body>
    <h1>🏃 STX Training - Week {week_num}</h1>
    <div class="subtitle"><strong>{phase}</strong></div>
    
    <div class="totals">
"""
    
    colors = {'Gold': 'gold', 'Green': 'green', 'White': 'white', 'Freshman': 'freshman'}
    for group in ['Gold', 'Green', 'White', 'Freshman']:
        color = colors[group]
        html += f"""        <div class="total {color}" onclick="filterGroup('{group}')" id="total-{group}">
            <div class="total-label">{group}</div>
            <div class="total-miles">{totals.get(group, 0):.0f}</div>
        </div>
"""
    
    html += """    </div>
    
    <div class="filters">
        <button class="filter-btn active" onclick="showAll()">Show All</button>
        <button class="filter-btn" onclick="filterGroup('Gold')">Gold</button>
        <button class="filter-btn" onclick="filterGroup('Green')">Green</button>
        <button class="filter-btn" onclick="filterGroup('White')">White</button>
        <button class="filter-btn" onclick="filterGroup('Freshman')">Freshman</button>
    </div>
    
"""
    
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_names = {'Mon': 'MONDAY', 'Tue': 'TUESDAY', 'Wed': 'WEDNESDAY', 'Thu': 'THURSDAY', 'Fri': 'FRIDAY', 'Sat': 'SATURDAY', 'Sun': 'SUNDAY'}
    
    for day in days_order:
        if day not in schedule:
            continue
            
        html += f"""    <div class="day">
        <div class="day-header">{day_names[day]}</div>
        <div class="day-content">
"""
        
        # Check if this day has status distinctions
        statuses = list(schedule[day].keys())
        has_status_split = len(statuses) > 1 or (len(statuses) == 1 and statuses[0] != 'normal')
        
        if has_status_split:
            # Day has Racer/Non-Racer split
            for status in ['Racer', 'Non-Racer']:
                if status not in schedule[day]:
                    continue
                
                # Display as "Racers" and "Non-Racers" (plural) in the output
                display_status = status + 's' if not status.endswith('s') else status
                
                html += f"""            <div class="status-section">
                <div class="status-title">{display_status}</div>
"""
                
                # PRE-WORK
                pre_work = set()
                for group in ['Gold', 'Green', 'White', 'Freshman']:
                    if group in schedule[day][status] and schedule[day][status][group]['pre']:
                        pre_work.add(schedule[day][status][group]['pre'])
                
                if pre_work:
                    html += f"""                <div class="section">
                    <div class="section-label">PRE-WORK</div>
                    <div class="pre-post">{', '.join(pre_work)}</div>
                </div>
"""
                
                # WORKOUT
                html += """                <div class="section">
                    <div class="section-label">WORKOUT</div>
"""
                
                for group in ['Gold', 'Green', 'White', 'Freshman']:
                    if group not in schedule[day][status]:
                        continue
                    
                    w = schedule[day][status][group]
                    color = colors[group]
                    miles_display = f"{w['miles']:.1f} mi" if w['miles'] > 0 else "REST"
                    main_workout = w['main'] or 'REST'
                    
                    html += f"""                    <div class="workout-item {color}" data-group="{group}">
                        <div class="group-badge {color}">{group}</div>
                        <div class="workout-desc">{main_workout}</div>
                        <div class="workout-miles">{miles_display}</div>
                    </div>
"""
                
                html += """                </div>
"""
                
                # POST-WORK
                post_work = set()
                for group in ['Gold', 'Green', 'White', 'Freshman']:
                    if group in schedule[day][status] and schedule[day][status][group]['post']:
                        post_work.add(schedule[day][status][group]['post'])
                
                if post_work:
                    html += f"""                <div class="section">
                    <div class="section-label">POST-WORK</div>
                    <div class="pre-post">{', '.join(post_work)}</div>
                </div>
"""
                
                html += """            </div>
"""
        
        else:
            # Normal day - no status distinction
            day_workouts = schedule[day]['normal']
            
            # PRE-WORK
            pre_work = set()
            for group in ['Gold', 'Green', 'White', 'Freshman']:
                if group in day_workouts and day_workouts[group]['pre']:
                    pre_work.add(day_workouts[group]['pre'])
            
            if pre_work:
                html += f"""            <div class="section">
                <div class="section-label">PRE-WORK</div>
                <div class="pre-post">{', '.join(pre_work)}</div>
            </div>
"""
            
            # WORKOUT
            html += """            <div class="section">
                <div class="section-label">WORKOUT</div>
"""
            
            for group in ['Gold', 'Green', 'White', 'Freshman']:
                if group not in day_workouts:
                    continue
                    
                w = day_workouts[group]
                color = colors[group]
                miles_display = f"{w['miles']:.1f} mi" if w['miles'] > 0 else "REST"
                main_workout = w['main'] or 'REST'
                
                html += f"""                <div class="workout-item {color}" data-group="{group}">
                    <div class="group-badge {color}">{group}</div>
                    <div class="workout-desc">{main_workout}</div>
                    <div class="workout-miles">{miles_display}</div>
                </div>
"""
            
            html += """            </div>
"""
            
            # POST-WORK
            post_work = set()
            for group in ['Gold', 'Green', 'White', 'Freshman']:
                if group in day_workouts and day_workouts[group]['post']:
                    post_work.add(day_workouts[group]['post'])
            
            if post_work:
                html += f"""            <div class="section">
                <div class="section-label">POST-WORK</div>
                <div class="pre-post">{', '.join(post_work)}</div>
            </div>
"""
        
        html += """        </div>
    </div>
"""
    
    html += """
    <script>
        let currentFilter = null;
        
        function filterGroup(group) {
            currentFilter = group;
            document.querySelectorAll('.workout-item').forEach(item => {
                item.classList.toggle('hidden', item.dataset.group !== group);
            });
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.total').forEach(t => t.classList.remove('active'));
            document.getElementById('total-' + group).classList.add('active');
        }
        
        function showAll() {
            currentFilter = null;
            document.querySelectorAll('.workout-item').forEach(item => item.classList.remove('hidden'));
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.filter-btn').classList.add('active');
            document.querySelectorAll('.total').forEach(t => t.classList.remove('active'));
        }
    </script>
</body>
</html>"""
    
    return html

def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_html_flexible.py <csv_file>")
        print("\nExample: python csv_to_html_flexible.py Week25_schedule.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Extract week number for output filename
    match = re.search(r'[Ww]eek[\s_-]?(\d+)', csv_file)
    if match:
        week_num = match.group(1)
    else:
        week_num = '25'
    
    # Generate and save
    html_output = generate_html(csv_file)
    output_file = f'week{week_num}_schedule.html'
    
    with open(output_file, 'w') as f:
        f.write(html_output)
    
    print(f"✅ Generated: {output_file}")
    print(f"📁 Open it in your browser to view the schedule")

if __name__ == "__main__":
    main()
