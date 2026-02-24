#!/usr/bin/env python3
"""
Generate weekly training schedule HTML with mileage ranges for racer/non-racer weeks.

Usage:
    python week_schedule_with_ranges.py week34_input.csv

Input CSV format:
    Day,Status,Group,Workout,Miles
    Monday,Racer,Gold,"10min WU; Hills - 40min; 10min CD",8.0
    Monday,Non-Racer,Gold,"8mi easy",7.0
    ...
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def parse_mileage(miles_str):
    """Parse mileage string, handling REST and numeric values."""
    if isinstance(miles_str, (int, float)):
        return float(miles_str)
    miles_str = str(miles_str).strip().upper()
    if miles_str == 'REST' or miles_str == '0' or not miles_str:
        return 0.0
    try:
        return float(miles_str)
    except ValueError:
        return 0.0


def calculate_group_totals(workouts):
    """
    Calculate racer and non-racer weekly mileage for each group.
    
    Racer total = days marked "Racer" + days marked "All" (or blank)
    Non-Racer total = days marked "Non-Racer" + days marked "All" (or blank)
    
    Returns dict of group -> (racer_miles, non_racer_miles)
    """
    # Track mileage by group and status
    group_mileage = defaultdict(lambda: {'Racer': 0.0, 'Non-Racer': 0.0, 'All': 0.0})
    
    for day, status, group, workout, miles in workouts:
        miles_val = parse_mileage(miles)
        group_mileage[group][status] += miles_val
    
    # Calculate totals
    totals = {}
    for group, mileage in group_mileage.items():
        racer_total = mileage['All'] + mileage['Racer']
        non_racer_total = mileage['All'] + mileage['Non-Racer']
        totals[group] = (racer_total, non_racer_total)
    
    return totals


def format_mileage_display(racer_miles, non_racer_miles):
    """Format mileage for display (show range if different, single value if same)."""
    if racer_miles == non_racer_miles:
        return str(int(racer_miles)) if racer_miles == int(racer_miles) else str(racer_miles)
    else:
        non_racer_str = str(int(non_racer_miles)) if non_racer_miles == int(non_racer_miles) else str(non_racer_miles)
        racer_str = str(int(racer_miles)) if racer_miles == int(racer_miles) else str(racer_miles)
        return f"{non_racer_str}-{racer_str}"


def generate_html(week_num, workouts, totals):
    """Generate complete HTML with mileage ranges."""
    
    # Group workouts by day and status
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    schedule = {day: {'Racer': [], 'Non-Racer': [], 'All': []} for day in days}
    
    for day, status, group, workout, miles in workouts:
        day_title = day.title()
        if day_title not in schedule:
            continue
        schedule[day_title][status].append((group, workout, miles))
    
    # Generate totals section
    groups = ['Gold', 'Green', 'White', 'Freshman']
    totals_html = []
    for group in groups:
        group_lower = group.lower()
        racer_miles, non_racer_miles = totals.get(group, (0, 0))
        display = format_mileage_display(racer_miles, non_racer_miles)
        totals_html.append(f'''        <div class="total {group_lower}" onclick="filterGroup('{group}')" id="total-{group}">
            <div class="total-label">{group}</div>
            <div class="total-miles">{display}</div>
        </div>''')
    
    # HTML template header
    html = f'''<!DOCTYPE html>
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
        .range-note {{ font-size: 0.7rem; color: #666; margin-top: 3px; }}
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
    <div class="subtitle"><strong>Training Week</strong></div>
    
    <div class="totals">
{chr(10).join(totals_html)}
    </div>
    
    <div class="filters">
        <button class="filter-btn active" onclick="showAll()">Show All</button>
        <button class="filter-btn" onclick="filterGroup('Gold')">Gold</button>
        <button class="filter-btn" onclick="filterGroup('Green')">Green</button>
        <button class="filter-btn" onclick="filterGroup('White')">White</button>
        <button class="filter-btn" onclick="filterGroup('Freshman')">Freshman</button>
    </div>
    '''
    
    # Generate day sections
    for day in days:
        if not any(schedule[day].values()):
            continue
            
        html += f'''
    <div class="day">
        <div class="day-header">{day.upper()}</div>
        <div class="day-content">'''
        
        # Handle different statuses (Racer, Non-Racer, All)
        for status in ['Racer', 'Non-Racer', 'All']:
            workouts_list = schedule[day][status]
            if not workouts_list:
                continue
            
            if status != 'All':
                html += f'''
            <div class="status-section">
                <div class="status-title">{status}s</div>'''
            
            # Group workouts by group
            html += '''
                <div class="section">
                    <div class="section-label">WORKOUT</div>'''
            
            for group, workout, miles in sorted(workouts_list, key=lambda x: groups.index(x[0]) if x[0] in groups else 999):
                group_lower = group.lower()
                miles_display = 'REST' if parse_mileage(miles) == 0 else f"{miles} mi"
                html += f'''
                    <div class="workout-item {group_lower}" data-group="{group}">
                        <div class="group-badge {group_lower}">{group}</div>
                        <div class="workout-desc">{workout}</div>
                        <div class="workout-miles">{miles_display}</div>
                    </div>'''
            
            html += '''
                </div>'''
            
            if status != 'All':
                html += '''
            </div>'''
        
        html += '''
        </div>
    </div>'''
    
    # Add JavaScript
    html += '''

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
</html>'''
    
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python week_schedule_with_ranges.py input.csv")
        print("\nCSV format:")
        print("Day,Status,Group,Workout,Miles")
        print("Monday,Racer,Gold,\"Hills workout\",8.0")
        print("Monday,Non-Racer,Gold,\"Easy run\",7.0")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    # Day name mapping for abbreviated days
    day_map = {
        'Mon': 'Monday',
        'Tue': 'Tuesday', 
        'Wed': 'Wednesday',
        'Thu': 'Thursday',
        'Fri': 'Friday',
        'Sat': 'Saturday',
        'Sun': 'Sunday'
    }
    
    # Parse CSV
    workouts = []
    with open(input_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle both 'Day' formats (full or abbreviated)
            day_raw = row.get('Day', '').strip()
            day = day_map.get(day_raw, day_raw)  # Convert abbreviation if needed
            
            status = row.get('Status', 'All').strip() or 'All'
            group = row.get('Group', '').strip()
            
            # Handle both 'Workout' and 'Main_Workout' column names
            workout = row.get('Workout', '').strip() or row.get('Main_Workout', '').strip()
            
            miles = row.get('Miles', '0').strip()
            
            if day and group and workout:
                workouts.append((day, status, group, workout, miles))
    
    if not workouts:
        print("Error: No valid workouts found in CSV")
        sys.exit(1)
    
    # Extract week number from filename
    week_num = ''.join(c for c in input_file.stem if c.isdigit()) or '1'
    
    # Calculate totals
    totals = calculate_group_totals(workouts)
    
    # Generate HTML
    html = generate_html(week_num, workouts, totals)
    
    # Write output
    output_file = input_file.stem + '_output.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✓ Generated {output_file}")
    print("\nWeekly Mileage:")
    print("Group      Racer    Non-Racer")
    print("-" * 35)
    for group in ['Gold', 'Green', 'White', 'Freshman']:
        racer_miles, non_racer_miles = totals.get(group, (0, 0))
        racer_str = f"{racer_miles:.0f}" if racer_miles == int(racer_miles) else f"{racer_miles:.1f}"
        non_racer_str = f"{non_racer_miles:.0f}" if non_racer_miles == int(non_racer_miles) else f"{non_racer_miles:.1f}"
        print(f"{group:9s}  {racer_str:>6s}   {non_racer_str:>6s}")


if __name__ == '__main__':
    main()
