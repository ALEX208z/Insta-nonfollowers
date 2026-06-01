#!/usr/bin/env python3
"""run_all.py

One-command pipeline runner for insta-nonfollowers.

  Step 1 — Parse your Instagram JSON exports into CSVs.
  Step 2 — (Optional) Enrich the non-followers list with follower counts.

Auto-detects followers_1.json and following.json in the project directory.

Usage:
    python run_all.py                   # Parse only  (no enrichment)
    python run_all.py --enrich          # Parse + enrich (public profiles)
    python run_all.py --enrich --login  # Parse + enrich (login for private accounts too)
    python run_all.py --enrich --resume # Resume enrichment from a previous run
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

ROOT = Path(__file__).parent


# ──────────────────────────────────────────────────────────────────────────────
# File auto-detection
# ──────────────────────────────────────────────────────────────────────────────

def find_json_files(keywords):
    """Recursively search for JSON files whose names contain any of the keywords."""
    matches = []
    for root, _, files in os.walk(ROOT):
        # Skip hidden dirs (like .git)
        if any(part.startswith(".") for part in Path(root).parts):
            continue
        for fname in files:
            if fname.lower().endswith(".json"):
                if any(kw in fname.lower() for kw in keywords):
                    matches.append(Path(root) / fname)
    return matches


def prompt_file_choice(matches, label):
    """Prompt the user to select a file from a list of candidates."""
    if len(matches) == 1:
        print(f"🔍  Auto-detected {label}: {matches[0]}")
        return matches[0]

    print(f"\n🔍  Found multiple candidates for {label}:")
    for i, m in enumerate(matches, 1):
        print(f"    [{i}] {m}")
    raw = input(f"Select [1–{len(matches)}] (Enter = 1): ").strip() or "1"
    try:
        return matches[int(raw) - 1]
    except (ValueError, IndexError):
        print("❌  Invalid choice.", file=sys.stderr)
        sys.exit(1)


def resolve_file(explicit_arg, keywords, label):
    """Return a resolved Path, either from the CLI arg or via auto-detection."""
    if explicit_arg:
        p = Path(explicit_arg)
        if not p.exists():
            print(f"❌  {label} not found: {p}", file=sys.stderr)
            sys.exit(1)
        return p

    matches = find_json_files(keywords)
    if not matches:
        print(f"\n❌  Could not find any {label} JSON file.", file=sys.stderr)
        print("    Export your data from Instagram: Settings → Your activity → Download your information", file=sys.stderr)
        sys.exit(1)

    return prompt_file_choice(matches, label)


# ──────────────────────────────────────────────────────────────────────────────
# Step runners
# ──────────────────────────────────────────────────────────────────────────────

def run_step(description, cmd):
    print(f"\n{'─'*54}")
    print(f"  {description}")
    print(f"{'─'*54}")
    print(f"  $ {' '.join(str(c) for c in cmd)}\n")
    subprocess.check_call(cmd)


def run_compare(followers_file, following_file, outdir):
    run_step("Step 1 / 2  —  Parsing JSON exports → CSV files", [
        sys.executable,
        str(ROOT / "compare_insta_json.py"),
        "--followers", str(followers_file),
        "--following", str(following_file),
        "--outdir",    str(outdir),
    ])


def run_enrich(input_csv, output_csv, login=False, delay=2.5, resume=False):
    cmd = [
        sys.executable,
        str(ROOT / "enrich_and_sort.py"),
        "--input",  str(input_csv),
        "--output", str(output_csv),
        "--delay",  str(delay),
    ]
    if login:
        cmd.append("--login")
    if resume:
        cmd.append("--resume")
    run_step("Step 2 / 2  —  Enriching non-followers with follower counts", cmd)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Full pipeline: parse Instagram JSON exports, then optionally enrich with follower counts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python run_all.py                          # parse only
  python run_all.py --enrich                 # parse + enrich (public profiles)
  python run_all.py --enrich --login         # parse + enrich (with private account access)
  python run_all.py --enrich --resume        # resume interrupted enrichment
        """,
    )
    parser.add_argument("--followers",  help="Path to followers JSON (auto-detected if omitted)")
    parser.add_argument("--following",  help="Path to following JSON (auto-detected if omitted)")
    parser.add_argument("--outdir",     default="output",   help="Output directory  (default: output/)")
    parser.add_argument("--enrich",     action="store_true", help="Run Step 2: fetch follower counts")
    parser.add_argument("--login",      action="store_true", help="Login to Instagram (for private accounts)")
    parser.add_argument("--delay",      type=float, default=2.5, help="Delay between requests  (default: 2.5s)")
    parser.add_argument("--resume",     action="store_true", help="Resume enrichment from existing partial output")
    args = parser.parse_args()

    print("\n🔎  insta-nonfollowers — pipeline starting\n")

    followers_path = resolve_file(args.followers, ["follower"],  "followers JSON")
    following_path = resolve_file(args.following, ["following"], "following JSON")

    outdir          = Path(args.outdir)
    not_following   = outdir / "not_following_back.csv"
    sorted_output   = outdir / "not_following_back_sorted.csv"

    # ── Step 1: parse
    run_compare(followers_path, following_path, outdir)

    # ── Step 2: enrich (optional)
    if args.enrich:
        run_enrich(not_following, sorted_output, login=args.login, delay=args.delay, resume=args.resume)
    else:
        print("\n💡  Tip: run with --enrich to also fetch follower counts and sort the non-followers list.")

    print(f"\n✅  Pipeline complete!  Output files are in: {outdir.resolve()}\n")


if __name__ == "__main__":
    main()
