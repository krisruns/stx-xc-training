#!/usr/bin/env python3
"""
Convert weekly training CSV to markdown format
Usage: python csv_to_markdown.py week12_schedule.csv
"""

import csv
from collections import defaultdict
import sys

def read_schedule(csv_file):
    """Read the CSV schedule file"""
    schedule = defaultdict(lambda: defaultdict(dict))
    totals = defaultdict(int)
    week_info = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            week = row['Week']
            day = row['Day']
            group = row['Group']
            
            # Store week number for header
            week_info['week'] = week
            
            # Store workout details
            schedule[day][group] = {
                'pre': row['Pre'],
                'main': row['Main_Workout'],
                'post': row['Post'],
                'miles': float(row['Miles']) if row['Miles'] else 0,
                'notes': row['Notes']
            }
            
            # Calculate totals
            totals[group] += float(row['Miles']) if row['Miles'] else 0
    
    return schedule, totals, week_info

def generate_markdown(schedule, totals, week_info):
    """Generate markdown from schedule data"""
    
    # Week header
    md = f"# Week {week_info['week']} Training Schedule\n"
    md += f"**August 11-17, 2025** • *Pre-Season Adjustment - School Starts*\n\n"
    
    # Weekly totals
    md += "## 📊 Weekly Mileage Totals\n"
    md += "| Gold | Green | White | Freshman |\n"
    md += "|:----:|:-----:|:-----:|:--------:|\n"
    md += f"| {totals['Gold']:.0f} mi | {totals['Green']:.0f} mi | {totals['White']:.0f} mi | {totals['Freshman']:.0f} mi |\n\n"
    
    # Day-by-day schedule
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_names = {
        'Mon': 'Monday',
        'Tue': 'Tuesday', 
        'Wed': 'Wednesday',
        'Thu': 'Thursday',
        'Fri': 'Friday',
        'Sat': 'Saturday',
        'Sun': 'Sunday'
    }
    
    for day in days_order:
        if day not in schedule:
            continue
            
        md += f"## {day_names[day]}\n\n"
        
        # Create table for the day
        md += "| Group | Pre | Main Workout | Post | Miles |\n"
        md += "|-------|-----|--------------|------|:-----:|\n"
        
        for group in ['Gold', 'Green', 'White', 'Freshman']:
            if group in schedule[day]:
                workout = schedule[day][group]
                pre = workout['pre'] or '—'
                main = workout['main'] or 'REST'
                post = workout['post'] or '—'
                miles = f"{workout['miles']:.1f}" if workout['miles'] > 0 else '—'
                
                md += f"| **{group}** | {pre} | {main} | {post} | {miles} |\n"
        
        md += "\n"
    
    # Footer with legend
    md += "---\n\n"
    md += "## 🔑 Key\n"
    md += "- **@E** = Easy pace (conversational)\n"
    md += "- **@T** = Threshold pace (comfortably hard, 15K-HM effort)\n"
    md += "- **@I** = Interval pace (3K-5K race effort)\n"
    md += "- **@R** = Repetition pace (mile pace or faster)\n\n"
    md += "**Pre-run:** Dynamics = dynamic warmup drills\n\n"
    md += "**Post-run:** Strides, Mobility A/B, Strength A/B, Drills\n"
    
    return md

def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_markdown.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Read and process
    schedule, totals, week_info = read_schedule(csv_file)
    
    # Generate markdown
    markdown = generate_markdown(schedule, totals, week_info)
    
    # Output to file
    output_file = f"week{week_info['week']}_schedule.md"
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    print(f"✅ Generated: {output_file}")
    print(markdown)

if __name__ == "__main__":
    main()
