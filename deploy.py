# deploy.py
# Run this when you're ready to publish updates to the STX XC site
import subprocess
import sys

def run(cmd, description=""):
    print(f"  → {description or ' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ Error: {result.stderr}")
        sys.exit(1)
    if result.stdout.strip():
        print(f"     {result.stdout.strip()}")
    return result

print("\n🚀 Deploying STX XC to GitHub Pages...\n")

# Show what's changed before committing
status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
if not status.stdout.strip():
    print("✅ Nothing to deploy - site is already up to date.")
    input("\nPress Enter to close...")
    sys.exit(0)

print("📋 Files to be uploaded:")
print(status.stdout)

# Confirm before pushing
confirm = input("Deploy these files? (y/n): ").strip().lower()
if confirm != 'y':
    print("Cancelled.")
    input("\nPress Enter to close...")
    sys.exit(0)

# Get a commit message
msg = input("Commit message (or press Enter for default): ").strip()
if not msg:
    from datetime import datetime
    msg = f"Update site - {datetime.now().strftime('%Y-%m-%d')}"

run(["git", "add", "."], "Staging all changes")
run(["git", "commit", "-m", msg], f"Committing: {msg}")
run(["git", "push", "origin", "main"], "Pushing to GitHub")

print("\n✅ Done! Site will be live in ~30 seconds.\n")
input("Press Enter to close...")
