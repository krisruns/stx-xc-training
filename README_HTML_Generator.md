# STX Training Groups HTML Generator

## Overview
This Python script generates a mobile-friendly HTML page displaying training groups from a CSV file of athlete data.

## Files Included
- `generate_groups_html.py` - Python script to generate HTML
- `athlete_groups.csv` - Input CSV with athlete data
- `athlete_groups.html` - Generated HTML output

## How to Use

### Prerequisites
- Python 3.x installed
- CSV file with columns: `Athlete`, `VDOT`, `Group`, `800m`, `Mile/1600m`, `3200m/2Mile`

### Running the Script

1. **Place the CSV file in the same directory as the script:**
   ```
   athlete_groups.csv
   ```

2. **Run the script:**
   ```bash
   python3 generate_groups_html.py
   ```

3. **Output file will be created:**
   ```
   athlete_groups.html
   ```

### Customizing the Script

To modify the input/output file paths, edit these lines in the script:

```python
# Input CSV file
with open('athlete_groups.csv', 'r') as f:

# Output HTML file
with open('athlete_groups.html', 'w') as f:
```

### HTML Features

The generated HTML includes:
- **Responsive design** - Works on mobile and desktop
- **Group cards** - Each training group in its own card
- **Clean athlete lists** - Just group numbers and athlete names
- **Hover effects** - Interactive elements for better UX
- **Mobile-friendly** - Stacks groups vertically on small screens

### Updating Groups

When you need to update the training groups:

1. Update the CSV file with new athlete data or group assignments
2. Run the Python script again
3. The HTML file will be regenerated with the new data

### CSV Format

The script expects a CSV with these columns:
```
Athlete,VDOT,Group,800m,Mile/1600m,3200m/2Mile
Nick Sanders,68,1,,4:27.2,
Marshall Wilson,65,1,2:02.4,,
```

- **Athlete** - Athlete's full name
- **VDOT** - Current VDOT value (integer)
- **Group** - Group number (1, 2, 3, etc.)
- **800m, Mile/1600m, 3200m/2Mile** - Best times at each distance (optional for HTML generation)

## Workflow

```
CSV Data → Python Script → HTML Page
```

This allows you to:
1. Maintain athlete data in a spreadsheet
2. Export as CSV
3. Generate updated HTML automatically
4. Upload HTML to your website

## Support

The script is designed to work with the St. Xavier XC/TF training group structure. Modify the styling in the HTML template section of the script to match your branding preferences.
