#!/usr/bin/env python3
"""
Generate track training schedule Excel workbook from revised mileage progression (4 groups)
"""

import pandas as pd

# Training data for Weeks 25-34 (4 groups only)
weeks_data = {
    25: {
        'dates': 'November 10-16, 2025',
        'phase': 'Base Building',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green': ('Easy', 3), 'Gold': ('Easy', 4)},
            'Tue': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 5), 'Gold': ('Easy', 6)},
            'Wed': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green': ('Easy', 3), 'Gold': ('Easy', 4)},
            'Thu': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 5), 'Gold': ('Easy', 6)},
            'Fri': {'Freshman': ('Easy', 2), 'White': ('Easy', 2), 'Green': ('Easy', 4), 'Gold': ('Easy', 4)},
            'Sat': {'Freshman': ('Long Run', 3), 'White': ('Long Run', 4), 'Green': ('Long Run', 5), 'Gold': ('Long Run', 6)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    26: {
        'dates': 'November 17-23, 2025',
        'phase': 'Thanksgiving Week',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green': ('Easy', 4), 'Gold': ('Easy', 5)},
            'Tue': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 7)},
            'Wed': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green': ('Easy', 4), 'Gold': ('Easy', 4)},
            'Thu': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 7)},
            'Fri': {'Freshman': ('Easy', 2), 'White': ('Easy', 3), 'Green': ('Easy', 4), 'Gold': ('Easy', 5)},
            'Sat': {'Freshman': ('Long Run', 4), 'White': ('Long Run', 5), 'Green': ('Long Run', 6), 'Gold': ('Long Run', 8)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    27: {
        'dates': 'November 24-30, 2025',
        'phase': 'Building Phase',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 5), 'Gold': ('Easy', 6)},
            'Tue': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Wed': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 4), 'Gold': ('Easy', 5)},
            'Thu': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Fri': {'Freshman': ('Easy', 3), 'White': ('Easy', 3), 'Green': ('Easy', 5), 'Gold': ('Easy', 6)},
            'Sat': {'Freshman': ('Long Run', 4), 'White': ('Long Run', 5), 'Green': ('Long Run', 7), 'Gold': ('Long Run', 9)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    28: {
        'dates': 'December 1-7, 2025',
        'phase': 'Continued Build',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 3), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 7)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green': ('Easy', 8), 'Gold': ('Easy', 9)},
            'Wed': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 5), 'Gold': ('Easy', 6)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green': ('Easy', 8), 'Gold': ('Easy', 9)},
            'Fri': {'Freshman': ('Easy', 3), 'White': ('Easy', 5), 'Green': ('Easy', 5), 'Gold': ('Easy', 7)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 6), 'Green': ('Long Run', 8), 'Gold': ('Long Run', 10)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    29: {
        'dates': 'December 8-14, 2025',
        'phase': 'Pre-Break Peak',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 10)},
            'Wed': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 7)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 10)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 8)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 7), 'Green': ('Long Run', 8), 'Gold': ('Long Run', 11)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    30: {
        'dates': 'December 15-21, 2025',
        'phase': 'Pre-Christmas Break',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 5), 'Gold': ('Easy', 6)},
            'Tue': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Wed': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 4), 'Gold': ('Easy', 5)},
            'Thu': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Fri': {'Freshman': ('Easy', 3), 'White': ('Easy', 4), 'Green': ('Easy', 5), 'Gold': ('Easy', 7)},
            'Sat': {'Freshman': ('Long Run', 4), 'White': ('Long Run', 6), 'Green': ('Long Run', 7), 'Gold': ('Long Run', 8)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    31: {
        'dates': 'December 22-28, 2025',
        'phase': 'Christmas Break Recovery',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 10)},
            'Wed': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 7)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 10)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 8)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 7), 'Green': ('Long Run', 8), 'Gold': ('Long Run', 11)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    32: {
        'dates': 'December 29, 2025 - January 4, 2026',
        'phase': 'Post-Break Build',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 10)},
            'Wed': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 7)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 10)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 5), 'Green': ('Easy', 6), 'Gold': ('Easy', 8)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 7), 'Green': ('Long Run', 8), 'Gold': ('Long Run', 11)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    33: {
        'dates': 'January 5-11, 2026',
        'phase': 'PEAK MILEAGE WEEK',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 9)},
            'Tue': {'Freshman': ('Easy', 6), 'White': ('Easy', 8), 'Green': ('Easy', 10), 'Gold': ('Easy', 11)},
            'Wed': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Thu': {'Freshman': ('Easy', 6), 'White': ('Easy', 8), 'Green': ('Easy', 10), 'Gold': ('Easy', 11)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 9)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 6), 'Green': ('Long Run', 9), 'Gold': ('Long Run', 12)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
    34: {
        'dates': 'January 12-18, 2026',
        'phase': 'Post-Peak Maintenance',
        'schedule': {
            'Mon': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 9)},
            'Tue': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 11)},
            'Wed': {'Freshman': ('Easy', 5), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Thu': {'Freshman': ('Easy', 5), 'White': ('Easy', 7), 'Green': ('Easy', 9), 'Gold': ('Easy', 11)},
            'Fri': {'Freshman': ('Easy', 4), 'White': ('Easy', 6), 'Green': ('Easy', 7), 'Gold': ('Easy', 8)},
            'Sat': {'Freshman': ('Long Run', 5), 'White': ('Long Run', 6), 'Green': ('Long Run', 9), 'Gold': ('Long Run', 11)},
            'Sun': {'Freshman': ('REST', 0), 'White': ('REST', 0), 'Green': ('REST', 0), 'Gold': ('REST', 0)},
        }
    },
}

def generate_excel_workbook():
    """Generate Excel workbook with all weeks as separate sheets"""
    with pd.ExcelWriter('STX_Track_Weeks_25-34_4Groups.xlsx', engine='openpyxl') as writer:
        for week_num in range(25, 35):
            week_data = weeks_data[week_num]
            rows = []
            
            # Create data for this week in v2 format
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                groups = week_data['schedule'][day]
                for group in ['Gold', 'Green', 'White', 'Freshman']:
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
                        'Status': '',  # Leave blank for normal days
                        'Pre': '',
                        'Main_Workout': main_workout,
                        'Post': '',
                        'Miles': miles if miles > 0 else 0,
                        'Notes': week_data['phase'] if day == 'Mon' and group == 'Gold' else ''
                    })
            
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name=f'Week {week_num}', index=False)
    
    print("✅ Generated: STX_Track_Weeks_25-34_4Groups.xlsx")

def main():
    print("Generating Excel workbook with 4 groups (Gold, Green, White, Freshman)...")
    generate_excel_workbook()
    print("\n✨ Excel file generated successfully!")
    print("   Each week is on a separate tab")
    print("   Format is ready for csv_to_html_v2.py and csv_to_markdown_v2.py")

if __name__ == "__main__":
    main()
