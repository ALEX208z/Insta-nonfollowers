#!/usr/bin/env python3
"""
run_all.py — Enhanced version

✅ Automatically detects followers_1.json and following.json
✅ Shows clear error messages if files missing
✅ Lets you run entire pipeline with one command:
    python run_all.py --login
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse

ROOT = Path(__file__).parent

# ---------------------- Helper: auto find JSON ----------------------
def find_json_file(possible_names):
    """Search recursively for a file whose name contains any keyword."""
    found = []
    for root, _, files in os.walk(ROOT):
        for f in files:
            if f.lower().endswith(".json"):
                name = f.lower()
                for keyword in possible_names:
                    if keyword in name:
                        found.append(Path(root) / f)
    return found

# ---------------------- Subprocess wrappers -------------------------
def run_compare(followers_file, following_file, outdir):
    cmd = [
        sys.executable,
        str(ROOT / "compare_insta_json.py"),
        "--followers", str(followers_file),
        "--following", str(following_file),
        "--outdir", str(outdir)
    ]
    print("\n📘 Step 1: Parsing JSONs to generate CSVs...")
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

def run_enrich(input_csv, output_csv, login=False, delay=2.0, resume=False):
    cmd = [
        sys.executable,
        str(ROOT / "enrich_and_sort.py"),
        "--input", str(input_csv),
        "--output", str(output_csv),
        "--delay", str(delay)
    ]
    if login:
        cmd.append("--login")
    if resume:
        cmd.append("--resume")
    print("\n📗 Step 2: Enriching and sorting by follower counts...")
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

# ---------------------- Main pipeline -------------------------------
def main():
    p = argparse.ArgumentParser(description="Run full pipeline for insta-nonfollowers")
    p.add_argument("--followers", help="Path to followers JSON (auto-detects if not provided)")
    p.add_argument("--following", help="Path to following JSON (auto-detects if not provided)")
    p.add_argument("--outdir", default="output", help="Output directory")
    p.add_argument("--login", action="store_true", help="Login to Instagram to access private accounts (recommended)")
    p.add_argument("--delay", type=float, default=2.0, help="Delay between profile requests (seconds)")
    p.add_argument("--resume", action="store_true", help="Resume enriching if partial output exists")
    args = p.parse_args()

    # Auto-find files if not provided
    followers_path = Path(args.followers) if args.followers else None
    following_path = Path(args.following) if args.following else None

    if not followers_path or not followers_path.exists():
        matches = find_json_file(["follower"])
        if matches:
            print(f"🔍 Found possible followers JSON(s):")
            for i, m in enumerate(matches, 1):
                print(f"  [{i}] {m}")
            choice = input(f"Select file [1-{len(matches)}] or press Enter for 1: ").strip() or "1"
            followers_path = matches[int(choice) - 1]
        else:
            print("❌ Could not find any followers JSON file (like followers_1.json).")
            print("Please export your data from Instagram and place it here.")
            sys.exit(1)

    if not following_path or not following_path.exists():
        matches = find_json_file(["following"])
        if matches:
            print(f"🔍 Found possible following JSON(s):")
            for i, m in enumerate(matches, 1):
                print(f"  [{i}] {m}")
            choice = input(f"Select file [1-{len(matches)}] or press Enter for 1: ").strip() or "1"
            following_path = matches[int(choice) - 1]
        else:
            print("❌ Could not find any following JSON file (like following.json).")
            print("Please export your data from Instagram and place it here.")
            sys.exit(1)

    # Output paths
    outdir = Path(args.outdir)
    not_following_csv = outdir / "not_following_back.csv"
    sorted_csv = outdir / "not_following_back_sorted.csv"

    # Step 1: compare
    run_compare(followers_path, following_path, outdir)

    # Step 2: enrich and sort
    print("\n✨ Now enriching with follower counts...")
    run_enrich(not_following_csv, sorted_csv, login=args.login, delay=args.delay, resume=args.resume)

    print("\n✅ All done! Results are in:", outdir.resolve())
    print("   - not_following_back.csv")
    print("   - not_following_back_sorted.csv")

if __name__ == "__main__":
    main()
