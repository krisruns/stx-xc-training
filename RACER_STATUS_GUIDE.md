# 🏃 Training Schedule System - Racer/Non-Racer Flexibility

## 🎯 Overview

Your training schedule system now supports **4 core groups** with **flexible Racer/Non-Racer splits** on race days.

**Core Groups:**
- 🟡 Gold
- 🟢 Green
- ⚪ White
- 🔵 Freshman

**On most days:** All groups train together (normal day)
**On race days:** Split into Racers and Non-Racers when needed

---

## 📋 CSV Format (Updated)

Your CSV now has a **Status** column:

```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
```

### **Status Column Values:**

| Value | When to Use |
|-------|-------------|
| *(blank)* | Normal training day - no racing distinction |
| `Racer` | This group is racing today |
| `Non-Racer` | This group is NOT racing today |

---

## 📝 Examples

### Example 1: Normal Training Day (No Race)

**Leave Status blank for all groups:**

```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
12,Mon,Gold,,Dynamics,8mi easy,Strides,8,
12,Mon,Green,,Dynamics,6.5mi easy,Strides,6.5,
12,Mon,White,,Dynamics,4.5mi easy,Strides,4.5,
12,Mon,Freshman,,Dynamics,2mi easy,Drills,2,
```

**Result:** All 4 groups shown together normally

---

### Example 2: Race Day - Some Groups Race, Others Don't

**Use Status column to split:**

```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
12,Sat,Gold,Racer,Dynamics,RACE - 5K,Cooldown,6,Trinity Invitational
12,Sat,Green,Racer,Dynamics,RACE - 5K,Cooldown,6,
12,Sat,White,Racer,Dynamics,RACE - 5K,Cooldown,6,
12,Sat,Freshman,Racer,Dynamics,RACE - 5K,Cooldown,5,
12,Sat,Gold,Non-Racer,Dynamics,Long Run 10mi,Mobility A,10,
12,Sat,Green,Non-Racer,Dynamics,Long Run 8mi,Mobility A,8,
12,Sat,White,Non-Racer,Dynamics,Long Run 6mi,Mobility A,6,
12,Sat,Freshman,Non-Racer,Dynamics,Long Run 4mi,Drills,4,
```

**Result:** Saturday will show TWO sections:
1. **Racers** - Gold, Green, White, Freshman (racing 5K)
2. **Non-Racers** - Gold, Green, White, Freshman (long run)

---

### Example 3: Varsity Only Racing

**Only some groups race:**

```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
12,Sat,Gold,Racer,Dynamics,RACE - 5K,Cooldown,6,Varsity only
12,Sat,Green,Racer,Dynamics,RACE - 5K,Cooldown,6,
12,Sat,White,Non-Racer,Dynamics,Tempo 5mi,Strides,6,JV workout
12,Sat,Freshman,Non-Racer,Dynamics,Long Run 4mi,Drills,5,
```

**Result:** 
- **Racers:** Gold, Green
- **Non-Racers:** White, Freshman

---

## 🖥️ Updated Scripts

### **Markdown Generator:**
```bash
python csv_to_markdown_v2.py week12_schedule.csv
```

### **HTML Generator:**
```bash
python csv_to_html_v2.py week12_schedule.csv
```

**Both scripts automatically:**
- ✅ Detect when Status is used
- ✅ Create separate Racer/Non-Racer sections
- ✅ Handle normal days (no Status) normally
- ✅ Work with any mix of racers/non-racers

---

## 📊 Output Examples

### Markdown Output (Saturday with split):

```markdown
## SATURDAY

### Racers

**PRE-WORK:** Dynamics

**WORKOUT:**
- 🟡 **Gold:** RACE - 5K — *6.0 mi*
- 🟢 **Green:** RACE - 5K — *6.0 mi*
- ⚪ **White:** RACE - 5K — *6.0 mi*
- 🔵 **Freshman:** RACE - 5K — *5.0 mi*

**POST-WORK:** Cooldown

### Non-Racers

**PRE-WORK:** Dynamics

**WORKOUT:**
- 🟡 **Gold:** Long Run 10mi — *10.0 mi*
- 🟢 **Green:** Long Run 8mi — *8.0 mi*
- ⚪ **White:** Long Run 6mi — *6.0 mi*
- 🔵 **Freshman:** Long Run 4mi — *4.0 mi*

**POST-WORK:** Mobility A, Drills
```

### HTML Output:
The HTML will display:
- Two visually distinct sections (Racers / Non-Racers)
- Each with its own Pre-Work, Workout, and Post-Work
- Filtering still works - click "Gold" to see Gold racers AND Gold non-racers
- Clean, separated layout

---

## 🎨 Visual Layout

**Normal Day (Monday-Friday typically):**
```
┌─────────────────────────┐
│      MONDAY             │
├─────────────────────────┤
│ PRE-WORK: Dynamics      │
│                         │
│ WORKOUT:                │
│ 🟡 Gold: 8mi easy       │
│ 🟢 Green: 6.5mi easy    │
│ ⚪ White: 4.5mi easy     │
│ 🔵 Freshman: 2mi easy   │
│                         │
│ POST-WORK: Strides      │
└─────────────────────────┘
```

**Race Day (Saturday with split):**
```
┌─────────────────────────┐
│      SATURDAY           │
├─────────────────────────┤
│ === RACERS ===          │
│ PRE-WORK: Dynamics      │
│ WORKOUT:                │
│ 🟡 Gold: RACE 5K        │
│ 🟢 Green: RACE 5K       │
│ ⚪ White: RACE 5K        │
│ 🔵 Freshman: RACE 5K    │
│ POST-WORK: Cooldown     │
├─────────────────────────┤
│ === NON-RACERS ===      │
│ PRE-WORK: Dynamics      │
│ WORKOUT:                │
│ 🟡 Gold: Long Run 10mi  │
│ 🟢 Green: Long Run 8mi  │
│ ⚪ White: Long Run 6mi   │
│ 🔵 Freshman: Long Run 4mi│
│ POST-WORK: Mobility A   │
└─────────────────────────┘
```

---

## 📁 Files You Need

### **Core Scripts (v2 - with Status support):**
- `csv_to_markdown_v2.py` - Markdown generator
- `csv_to_html_v2.py` - HTML generator

### **Example Files:**
- `week12_with_racers.csv` - Sample CSV showing Status usage

### **Old Scripts (still work for simple schedules):**
- `csv_to_markdown.py` - Original markdown (no Status support)
- `csv_to_html.py` - Original HTML (no Status support)

---

## 🔄 Workflow

### Creating a Week with Race Day:

**1. Start with your template:**
```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
12,Mon,Gold,,Dynamics,8mi easy,Strides,8,
12,Mon,Green,,Dynamics,6.5mi easy,Strides,6.5,
...
```

**2. Add race day (Saturday):**
```csv
12,Sat,Gold,Racer,Dynamics,RACE - 5K,Cooldown,6,Trinity Invite
12,Sat,Green,Racer,Dynamics,RACE - 5K,Cooldown,6,
12,Sat,White,Racer,Dynamics,RACE - 5K,Cooldown,6,
12,Sat,Freshman,Racer,Dynamics,RACE - 5K,Cooldown,5,
12,Sat,Gold,Non-Racer,Dynamics,Long Run 10mi,Mobility A,10,
12,Sat,Green,Non-Racer,Dynamics,Long Run 8mi,Mobility A,8,
12,Sat,White,Non-Racer,Dynamics,Long Run 6mi,Mobility A,6,
12,Sat,Freshman,Non-Racer,Dynamics,Long Run 4mi,Drills,4,
```

**3. Generate outputs:**
```bash
python csv_to_markdown_v2.py week12_schedule.csv
python csv_to_html_v2.py week12_schedule.csv
```

**4. Done!** You have both markdown and HTML with proper Racer/Non-Racer sections.

---

## 💡 Use Cases

### When to Use Status Column:

✅ **Invitational meets** - Some athletes racing, others doing long run  
✅ **JV-only meets** - Varsity doing workout while JV races  
✅ **Split squad meets** - Different groups at different meets  
✅ **Dual meets** - Some athletes resting while others compete  
✅ **Time trials** - Testing some athletes while others train normally  

### When NOT to Use Status:

❌ **Normal training days** - Everyone doing same type of work  
❌ **Championship meets** - Everyone competing (use Notes to say "CHAMPIONSHIPS")  
❌ **Rest days** - Just put REST in Main_Workout  

---

## 🎯 Pro Tips

### Tip 1: Weekly Mileage Calculation
The scripts automatically total ALL mileage for each group, whether they're racing or not. A Gold athlete who races 6mi still gets 6mi counted in their weekly total.

### Tip 2: Mixing Status on Same Day
You CAN have different Status values for different groups on the same day:
- Gold: Racer
- Green: Racer  
- White: Non-Racer
- Freshman: Non-Racer

### Tip 3: Notes Field
Use the Notes field to add context:
```csv
12,Sat,Gold,Racer,Dynamics,RACE - 5K,Cooldown,6,Trinity Invitational
```

### Tip 4: Keep It Simple
You don't NEED to use Status every race day. If everyone is racing:
```csv
12,Sat,Gold,,Dynamics,RACE - 5K,Cooldown,6,Everyone racing today
```

---

## ⚙️ Technical Details

### How the Scripts Detect Status:

1. Read CSV and check for Status column values
2. For each day:
   - If ANY row has a Status value → Use split view (Racers/Non-Racers)
   - If NO rows have Status values → Use normal view
3. Group workouts by Status, then by Group
4. Generate separate sections for each Status

### Status Values Are Case-Sensitive:
- ✅ `Racer` (correct)
- ✅ `Non-Racer` (correct)
- ❌ `racer` (won't work)
- ❌ `NonRacer` (won't work)

---

## 🆘 Troubleshooting

**Q: My Status split isn't showing up**  
A: Make sure you're using `csv_to_markdown_v2.py` and `csv_to_html_v2.py` (v2 versions)

**Q: I see blank sections**  
A: Check that Status values are exactly `Racer` or `Non-Racer` (case-sensitive)

**Q: Can I have 3 groups?**  
A: Status only supports 2 categories. For 3+, you'd need different Status values (e.g., "Racer-Varsity", "Racer-JV", "Non-Racer")

**Q: Does this work with track schedules?**  
A: Yes! The v2 scripts work for any schedule with 4 groups

---

## 📚 Quick Reference

```bash
# GENERATE MARKDOWN
python csv_to_markdown_v2.py week12_schedule.csv

# GENERATE HTML  
python csv_to_html_v2.py week12_schedule.csv

# GENERATE BOTH
python csv_to_markdown_v2.py week12_schedule.csv && python csv_to_html_v2.py week12_schedule.csv
```

---

That's it! You now have maximum flexibility with 4 core groups plus Racer/Non-Racer splits when you need them.
