#!/usr/bin/env python3
"""
Generate track training schedule CSVs and Excel workbook from mileage progression
"""

import csv
import pandas as pd
from collections import defaultdict

# Training data for Weeks 25-34
weeks_data = {
    25: {
        'dates': 'November 10-16, 2025',
        'phase': 'JV Base Building',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green JV': ('Easy', 3), 'Green Varsity': ('REST', 0), 'Gold JV': ('Easy', 4), 'Gold Varsity': ('REST', 0)},
            'Tue': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 5), 'Green Varsity': ('REST', 0), 'Gold JV': ('Easy', 6), 'Gold Varsity': ('REST', 0)},
            'Wed': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green JV': ('Easy', 3), 'Green Varsity': ('REST', 0), 'Gold JV': ('Easy', 4), 'Gold Varsity': ('REST', 0)},
            'Thu': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 5), 'Green Varsity': ('REST', 0), 'Gold JV': ('Easy', 6), 'Gold Varsity': ('REST', 0)},
            'Fri': {'Freshman': ('Easy', 2), 'White': ('Easy', 2), 'Green JV': ('Easy', 4), 'Green Varsity': ('REST', 0), 'Gold JV': ('Easy', 4), 'Gold Varsity': ('REST', 0)},
            'Sat': {'Freshman': ('Long Run', 3), 'White': ('Long Run', 4), 'Green JV': ('Long Run', 5), 'Green Varsity': ('REST', 0), 'Gold JV': ('Long Run', 6), 'Gold Varsity': ('REST', 0)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    26: {
        'dates': 'November 17-23, 2025',
        'phase': 'Varsity Enters (Thanksgiving Week)',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green JV': ('Easy', 4), 'Green Varsity': ('Easy', 3), 'Gold JV': ('Easy', 5), 'Gold Varsity': ('Easy', 3)},
            'Tue': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 5)},
            'Wed': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green JV': ('Easy', 4), 'Green Varsity': ('Easy', 2), 'Gold JV': ('Easy', 4), 'Gold Varsity': ('Easy', 3)},
            'Thu': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 5)},
            'Fri': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green JV': ('Easy', 4), 'Green Varsity': ('Easy', 3), 'Gold JV': ('Easy', 5), 'Gold Varsity': ('Easy', 3)},
            'Sat': {'Freshman': ('Long Run', 4), 'White': ('Long Run', 5), 'Green JV': ('Long Run', 6), 'Green Varsity': ('Long Run', 4), 'Gold JV': ('Long Run', 8), 'Gold Varsity': ('Long Run', 6)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    27: {
        'dates': 'November 24-30, 2025',
        'phase': 'Building Phase',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 5), 'Green Varsity': ('Easy', 3), 'Gold JV': ('Easy', 6), 'Gold Varsity': ('Easy', 4)},
            'Tue': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Wed': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 4), 'Green Varsity': ('Easy', 3), 'Gold JV': ('Easy', 5), 'Gold Varsity': ('Easy', 4)},
            'Thu': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Fri': {'Freshman': ('Easy', 3), 'White': ('Easy', 3), 'Green JV': ('Easy', 5), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 6), 'Gold Varsity': ('Easy', 4)},
            'Sat': {'Freshman': ('Long Run', 4), 'White': ('Long Run', 5), 'Green JV': ('Long Run', 7), 'Green Varsity': ('Long Run', 5), 'Gold JV': ('Long Run', 9), 'Gold Varsity': ('Long Run', 6)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    28: {
        'dates': 'December 1-7, 2025',
        'phase': 'Continued Build',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 3), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 5)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green JV': ('Easy', 8), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 9), 'Gold Varsity': ('Easy', 7)},
            'Wed': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 5), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 6), 'Gold Varsity': ('Easy', 4)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green JV': ('Easy', 8), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 9), 'Gold Varsity': ('Easy', 7)},
            'Fri': {'Freshman': ('Easy', 3), 'White': ('Easy', 5), 'Green JV': ('Easy', 5), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 5)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 6), 'Green JV': ('Long Run', 8), 'Green Varsity': ('Long Run', 6), 'Gold JV': ('Long Run', 10), 'Gold Varsity': ('Long Run', 7)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    29: {
        'dates': 'December 8-14, 2025',
        'phase': 'Pre-Break Peak',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 10), 'Gold Varsity': ('Easy', 8)},
            'Wed': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 5)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 10), 'Gold Varsity': ('Easy', 8)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 5)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 7), 'Green JV': ('Long Run', 8), 'Green Varsity': ('Long Run', 7), 'Gold JV': ('Long Run', 11), 'Gold Varsity': ('Long Run', 8)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    30: {
        'dates': 'December 15-21, 2025',
        'phase': 'Pre-Christmas Break',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 5), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 6), 'Gold Varsity': ('Easy', 4)},
            'Tue': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Wed': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 4), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 5), 'Gold Varsity': ('Easy', 4)},
            'Thu': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Fri': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green JV': ('Easy', 5), 'Green Varsity': ('Easy', 4), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 5)},
            'Sat': {'Freshman': ('Long Run', 4), 'White': ('Long Run', 6), 'Green JV': ('Long Run', 7), 'Green Varsity': ('Long Run', 6), 'Gold JV': ('Long Run', 8), 'Gold Varsity': ('Long Run', 7)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    31: {
        'dates': 'December 22-28, 2025',
        'phase': 'Christmas Break Recovery',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 10), 'Gold Varsity': ('Easy', 8)},
            'Wed': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 6)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 10), 'Gold Varsity': ('Easy', 8)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 7), 'Green JV': ('Long Run', 8), 'Green Varsity': ('Long Run', 8), 'Gold JV': ('Long Run', 11), 'Gold Varsity': ('Long Run', 9)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    32: {
        'dates': 'December 29, 2025 - January 4, 2026',
        'phase': 'Post-Break Build',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 10), 'Gold Varsity': ('Easy', 8)},
            'Wed': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 5), 'Gold JV': ('Easy', 7), 'Gold Varsity': ('Easy', 6)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 10), 'Gold Varsity': ('Easy', 8)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green JV': ('Easy', 6), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 6)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 7), 'Green JV': ('Long Run', 8), 'Green Varsity': ('Long Run', 8), 'Gold JV': ('Long Run', 11), 'Gold Varsity': ('Long Run', 9)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    33: {
        'dates': 'January 5-11, 2026',
        'phase': 'PEAK MILEAGE WEEK',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 9), 'Gold Varsity': ('Easy', 7)},
            'Tue': {'Freshman': ('Easy', 6), 'White': ('Easy', 8), 'Green JV': ('Easy', 10), 'Green Varsity': ('Easy', 8), 'Gold JV': ('Easy', 11), 'Gold Varsity': ('Easy', 9)},
            'Wed': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 7)},
            'Thu': {'Freshman': ('Easy', 6), 'White': ('Easy', 8), 'Green JV': ('Easy', 10), 'Green Varsity': ('Easy', 8), 'Gold JV': ('Easy', 11), 'Gold Varsity': ('Easy', 9)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 7), 'Gold JV': ('Easy', 9), 'Gold Varsity': ('Easy', 8)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 6), 'Green JV': ('Long Run', 9), 'Green Varsity': ('Long Run', 9), 'Gold JV': ('Long Run', 12), 'Gold Varsity': ('Long Run', 10)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
    34: {
        'dates': 'January 12-18, 2026',
        'phase': 'Post-Peak Maintenance',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 9), 'Gold Varsity': ('Easy', 7)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 8), 'Gold JV': ('Easy', 11), 'Gold Varsity': ('Easy', 9)},
            'Wed': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 7)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green JV': ('Easy', 9), 'Green Varsity': ('Easy', 8), 'Gold JV': ('Easy', 11), 'Gold Varsity': ('Easy', 9)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green JV': ('Easy', 7), 'Green Varsity': ('Easy', 6), 'Gold JV': ('Easy', 8), 'Gold Varsity': ('Easy', 7)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 6), 'Green JV': ('Long Run', 9), 'Green Varsity': ('Long Run', 9), 'Gold JV': ('Long Run', 11), 'Gold Varsity': ('Long Run', 10)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green JV': ('REST', 0), 'Green Varsity': ('REST', 0), 'Gold JV': ('REST', 0), 'Gold Varsity': ('REST', 0)},
        }
    },
}

def generate_week_csv(week_num):
    """Generate CSV for a single week"""
    week_data = weeks_data[week_num]
    rows = []
    
    for day, groups in week_data['schedule'].items():
        for group, (workout_type, miles) in groups.items():
            if workout_type == 'REST':
                main_workout = 'REST'
            elif workout_type == 'Long Run':
                main_workout = f'Long Run {miles}mi'
            else:
                main_workout = f'{miles}mi easy'
            
            rows.append({
                'Week': week_num,
                'Day': day,
                'Group': group,
                'Pre': '',
                'Main_Workout': main_workout,
                'Post': '',
                'Miles': miles if miles > 0 else 0,
                'Notes': week_data['phase'] if day == 'Mon' else ''
            })
    
    # Write CSV
    filename = f'week{week_num}_schedule.csv'
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Week', 'Day', 'Group', 'Pre', 'Main_Workout', 'Post', 'Miles', 'Notes'])
        writer.writeheader()
        writer.writerows(rows)
    
    return filename

def generate_excel_workbook():
    """Generate Excel workbook with all weeks as separate sheets"""
    with pd.ExcelWriter('track_training_weeks_25-34.xlsx', engine='openpyxl') as writer:
        for week_num in range(25, 35):
            week_data = weeks_data[week_num]
            rows = []
            
            # Create data for this week
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                groups = week_data['schedule'][day]
                for group in ['Freshman', 'White', 'Green JV', 'Green Varsity', 'Gold JV', 'Gold Varsity']:
                    workout_type, miles = groups[group]
                    if workout_type == 'REST':
                        main_workout = 'REST'
                    elif workout_type == 'Long Run':
                        main_workout = f'Long Run {miles}mi'
                    else:
                        main_workout = f'{miles}mi easy'
                    
                    rows.append({
                        'Week': week_num,
                        'Day': day,
                        'Group': group,
                        'Pre': '',
                        'Main_Workout': main_workout,
                        'Post': '',
                        'Miles': miles if miles > 0 else 0,
                        'Notes': week_data['phase'] if day == 'Mon' else ''
                    })
            
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name=f'Week {week_num}', index=False)
    
    print("✅ Generated: track_training_weeks_25-34.xlsx")

def main():
    # Generate individual CSVs
    print("Generating individual CSV files...")
    for week_num in range(25, 35):
        filename = generate_week_csv(week_num)
        print(f"✅ Generated: {filename}")
    
    # Generate Excel workbook
    print("\nGenerating Excel workbook...")
    generate_excel_workbook()
    
    print("\n✨ All files generated successfully!")

if __name__ == "__main__":
    main()
