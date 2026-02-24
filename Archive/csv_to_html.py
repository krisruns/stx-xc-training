#!/usr/bin/env python3
"""
Convert weekly training CSV to simple filterable HTML
"""

import csv
from collections import defaultdict

def generate_html(csv_file):
    """Generate simple, filterable HTML from CSV"""
    
    # Read CSV
    schedule = defaultdict(lambda: defaultdict(dict))
    totals = defaultdict(int)
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            day = row['Day']
            group = row['Group']
            schedule[day][group] = {
                'pre': row['Pre'],
                'main': row['Main_Workout'],
                'post': row['Post'],
                'miles': float(row['Miles']) if row['Miles'] else 0
            }
            totals[group] += float(row['Miles']) if row['Miles'] else 0
    
    # Generate HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX XC Week 12 Training</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 1200px; margin: 20px auto; padding: 0 20px; }
        h1 { color: #2c5530; border-bottom: 3px solid #4a7c59; padding-bottom: 10px; }
        .totals { display: flex; gap: 15px; margin: 20px 0; }
        .total { padding: 15px; background: #f0f4f1; border-left: 4px solid #4a7c59; border-radius: 4px; flex: 1; text-align: center; cursor: pointer; transition: all 0.2s; }
        .total:hover { background: #e0ebe2; transform: translateY(-2px); }
        .total.active { background: #4a7c59; color: white; }
        .total-label { font-size: 0.9rem; font-weight: 600; text-transform: uppercase; }
        .total-miles { font-size: 1.5rem; font-weight: 700; }
        .filters { margin: 20px 0; }
        .filter-btn { padding: 8px 16px; margin: 0 5px 5px 0; border: 2px solid #4a7c59; background: white; color: #4a7c59; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
        .filter-btn:hover, .filter-btn.active { background: #4a7c59; color: white; }
        .day { margin: 25px 0; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; }
        .day-header { background: #f5f7f6; padding: 12px 20px; font-size: 1.1rem; font-weight: 600; color: #2c5530; }
        .workout { padding: 15px 20px; border-bottom: 1px solid #f0f0f0; display: grid; grid-template-columns: 100px 1fr 120px; gap: 15px; align-items: center; }
        .workout:last-child { border-bottom: none; }
        .workout.hidden { display: none; }
        .group-name { font-weight: 700; color: #2c5530; text-transform: uppercase; }
        .workout-main { font-size: 0.95rem; }
        .workout-details { font-size: 0.85rem; color: #666; margin-top: 4px; }
        .miles { font-weight: 700; text-align: right; color: #4a7c59; }
        @media (max-width: 768px) {
            .totals { flex-direction: column; }
            .workout { grid-template-columns: 1fr; gap: 8px; }
            .miles { text-align: left; }
        }
    </style>
</head>
<body>
    <h1>STX XC Training - Week 12</h1>
    <p><strong>August 11-17, 2025</strong> • Pre-Season Adjustment - School Starts</p>
    
    <div class="totals">
"""
    
    for group in ['Gold', 'Green', 'White', 'Freshman']:
        html += f"""        <div class="total" onclick="filterGroup('{group}')" id="total-{group}">
            <div class="total-label">{group}</div>
            <div class="total-miles">{totals[group]:.0f} mi</div>
        </div>
"""
    
    html += """    </div>
    
    <div class="filters">
        <button class="filter-btn active" onclick="showAll()">Show All</button>
        <button class="filter-btn" onclick="filterGroup('Freshman')">Freshman</button>
        <button class="filter-btn" onclick="filterGroup('White')">White</button>
        <button class="filter-btn" onclick="filterGroup('Green')">Green</button>
        <button class="filter-btn" onclick="filterGroup('Gold')">Gold</button>
    </div>
    
"""
    
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_names = {'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday', 'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday', 'Sun': 'Sunday'}
    
    for day in days_order:
        if day not in schedule:
            continue
            
        html += f"""    <div class="day">
        <div class="day-header">{day_names[day]}</div>
"""
        
        for group in ['Gold', 'Green', 'White', 'Freshman']:
            if group not in schedule[day]:
                continue
                
            w = schedule[day][group]
            pre_post = []
            if w['pre']: pre_post.append(w['pre'])
            if w['post']: pre_post.append(w['post'])
            details = ' • '.join(pre_post) if pre_post else ''
            
            miles_display = f"{w['miles']:.1f} mi" if w['miles'] > 0 else "—"
            
            html += f"""        <div class="workout" data-group="{group}">
            <div class="group-name">{group}</div>
            <div>
                <div class="workout-main">{w['main'] or 'REST'}</div>
                {f'<div class="workout-details">{details}</div>' if details else ''}
            </div>
            <div class="miles">{miles_display}</div>
        </div>
"""
        
        html += """    </div>
"""
    
    html += """
    <script>
        let currentFilter = null;
        
        function filterGroup(group) {
            currentFilter = group;
            document.querySelectorAll('.workout').forEach(w => {
                w.classList.toggle('hidden', w.dataset.group !== group);
            });
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.total').forEach(t => t.classList.remove('active'));
            document.getElementById('total-' + group).classList.add('active');
        }
        
        function showAll() {
            currentFilter = null;
            document.querySelectorAll('.workout').forEach(w => w.classList.remove('hidden'));
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.filter-btn').classList.add('active');
            document.querySelectorAll('.total').forEach(t => t.classList.remove('active'));
        }
    </script>
</body>
</html>"""
    
    return html

# Generate and save
html_output = generate_html('week12_schedule.csv')
with open('week12_schedule.html', 'w') as f:
    f.write(html_output)

print("✅ Generated: week12_schedule.html")
