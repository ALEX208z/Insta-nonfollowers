#!/usr/bin/env python3
"""compare_insta_json.py
Parse Instagram exported JSON files and produce CSVs:
 - output/not_following_back.csv
 - output/followers_only.csv
 - output/mutuals.csv

Usage:
    python compare_insta_json.py --followers followers_1.json --following following.json
"""
import json
import csv
import argparse
from pathlib import Path

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_followers_from_followers_json(data):
    """followers_1.json format:
       top-level is a list; each item has string_list_data -> [{ 'value': username, ...}, ...]
    """
    usernames = set()
    if not isinstance(data, list):
        return usernames
    for entry in data:
        try:
            sld = entry.get("string_list_data", [])
            if sld and isinstance(sld, list) and isinstance(sld[0].get("value"), str):
                usernames.add(sld[0]["value"].strip().lower())
        except Exception:
            continue
    return usernames

def extract_following_from_following_json(data):
    """following.json format:
       top-level contains 'relationships_following' which is a list of objects with 'title' = username
    """
    usernames = set()
    if isinstance(data, dict):
        rel = data.get("relationships_following") or data.get("following") or []
        if isinstance(rel, list):
            for entry in rel:
                title = entry.get("title")
                if isinstance(title, str) and title.strip():
                    usernames.add(title.strip().lower())
    return usernames

def write_csv(path: Path, usernames, include_link=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if include_link:
            w.writerow(["username", "profile_link"])
            for u in sorted(usernames):
                w.writerow([u, f"https://www.instagram.com/{u}"])
        else:
            w.writerow(["username"])
            for u in sorted(usernames):
                w.writerow([u])

def main():
    p = argparse.ArgumentParser(description="Compare Instagram exported followers/following JSONs.")
    p.add_argument("--followers", "-f", required=True, help="Path to followers JSON (e.g. followers_1.json)")
    p.add_argument("--following", "-g", required=True, help="Path to following JSON (e.g. following.json)")
    p.add_argument("--outdir", "-o", default="output", help="Output directory")
    args = p.parse_args()

    followers_path = Path(args.followers)
    following_path = Path(args.following)
    outdir = Path(args.outdir)

    raw_followers = load_json(followers_path)
    raw_following = load_json(following_path)

    followers = extract_followers_from_followers_json(raw_followers)
    following = extract_following_from_following_json(raw_following)

    not_following_back = following - followers
    followers_only = followers - following
    mutuals = followers & following

    write_csv(outdir / "not_following_back.csv", not_following_back)
    write_csv(outdir / "followers_only.csv", followers_only)
    write_csv(outdir / "mutuals.csv", mutuals)

    print("✅ Done.")
    print(f"Not following back: {len(not_following_back)} -> {outdir / 'not_following_back.csv'}")
    print(f"Followers only: {len(followers_only)} -> {outdir / 'followers_only.csv'}")
    print(f"Mutuals: {len(mutuals)} -> {outdir / 'mutuals.csv'}")

if __name__ == "__main__":
    main()
