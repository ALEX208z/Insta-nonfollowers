#!/usr/bin/env python3
"""compare_insta_json.py

Parse Instagram exported JSON files and produce three CSVs:
  - output/not_following_back.csv  — accounts you follow who don't follow back
  - output/followers_only.csv      — accounts that follow you, but you don't follow
  - output/mutuals.csv             — mutual followers

Supports Instagram data export formats from 2023 onward.

Usage:
    python compare_insta_json.py --followers followers_1.json --following following.json
    python compare_insta_json.py -f followers_1.json -g following.json --outdir my_output
"""

import json
import csv
import argparse
import sys
from pathlib import Path
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────────
# JSON loaders
# ──────────────────────────────────────────────────────────────────────────────

def load_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌  File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌  Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_followers(data):
    """
    followers_1.json (Instagram export ≥2023):
      Top-level list; each item has string_list_data -> [{ value: username, ... }]
    """
    usernames = set()
    if not isinstance(data, list):
        print("⚠️  Unexpected followers format — expected a top-level list.", file=sys.stderr)
        return usernames
    for entry in data:
        try:
            sld = entry.get("string_list_data", [])
            if sld and isinstance(sld, list):
                value = sld[0].get("value", "").strip().lower()
                if value:
                    usernames.add(value)
        except Exception:
            continue
    return usernames


def extract_following(data):
    """
    following.json (Instagram export ≥2023):
      { "relationships_following": [ { "title": username, ... }, ... ] }
    Also handles legacy list format (same structure as followers).
    """
    usernames = set()

    if isinstance(data, dict):
        rel = data.get("relationships_following") or data.get("following") or []
        if isinstance(rel, list):
            for entry in rel:
                title = entry.get("title", "").strip().lower()
                if title:
                    usernames.add(title)
        return usernames

    # Legacy / alternative format: top-level list
    if isinstance(data, list):
        for entry in data:
            try:
                sld = entry.get("string_list_data", [])
                if sld and isinstance(sld, list):
                    value = sld[0].get("value", "").strip().lower()
                    if value:
                        usernames.add(value)
            except Exception:
                continue

    return usernames


# ──────────────────────────────────────────────────────────────────────────────
# CSV writer
# ──────────────────────────────────────────────────────────────────────────────

def write_csv(path: Path, usernames):
    """Write a sorted CSV with username and clickable Instagram profile link."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "profile_link"])
        for username in sorted(usernames):
            writer.writerow([username, f"https://www.instagram.com/{username}/"])


# ──────────────────────────────────────────────────────────────────────────────
# Pretty summary
# ──────────────────────────────────────────────────────────────────────────────

def print_summary(followers, following, not_following_back, followers_only, mutuals, outdir):
    w = 54
    print()
    print("─" * w)
    print("  📊  Instagram Follower Analysis")
    print(f"  {'Generated:':<22} {datetime.now().strftime('%Y-%m-%d  %H:%M')}")
    print("─" * w)
    print(f"  {'You follow:':<32} {len(following):>5}")
    print(f"  {'Follow you:':<32} {len(followers):>5}")
    print("─" * w)
    print(f"  {'✅  Mutuals:':<32} {len(mutuals):>5}  → mutuals.csv")
    print(f"  {'❌  Not following back:':<32} {len(not_following_back):>5}  → not_following_back.csv")
    print(f"  {'👀  You don\'t follow back:':<32} {len(followers_only):>5}  → followers_only.csv")
    print("─" * w)
    if len(following) > 0:
        ratio = len(mutuals) / len(following) * 100
        print(f"  {'Mutual rate:':<32} {ratio:>4.1f}%")
    print(f"  {'Output folder:':<32} {outdir.resolve()}")
    print("─" * w)
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compare Instagram followers/following JSON exports and output CSVs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python compare_insta_json.py --followers followers_1.json --following following.json
  python compare_insta_json.py -f followers_1.json -g following.json --outdir results/
        """,
    )
    parser.add_argument("--followers", "-f", required=True,
                        help="Path to followers JSON  (e.g. followers_1.json)")
    parser.add_argument("--following", "-g", required=True,
                        help="Path to following JSON  (e.g. following.json)")
    parser.add_argument("--outdir",   "-o", default="output",
                        help="Output directory  (default: output/)")
    args = parser.parse_args()

    followers_path = Path(args.followers)
    following_path = Path(args.following)
    outdir         = Path(args.outdir)

    print(f"\n📂  Loading {followers_path.name} ...")
    raw_followers = load_json(followers_path)
    followers     = extract_followers(raw_followers)

    print(f"📂  Loading {following_path.name} ...")
    raw_following = load_json(following_path)
    following     = extract_following(raw_following)

    if not followers:
        print("⚠️  No followers found. Verify this is a valid Instagram export.", file=sys.stderr)
    if not following:
        print("⚠️  No following found. Verify this is a valid Instagram export.", file=sys.stderr)

    not_following_back = following - followers
    followers_only     = followers - following
    mutuals            = followers & following

    write_csv(outdir / "not_following_back.csv", not_following_back)
    write_csv(outdir / "followers_only.csv",     followers_only)
    write_csv(outdir / "mutuals.csv",            mutuals)

    print_summary(followers, following, not_following_back, followers_only, mutuals, outdir)


if __name__ == "__main__":
    main()
