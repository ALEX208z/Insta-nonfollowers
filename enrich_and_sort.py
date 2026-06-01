#!/usr/bin/env python3
"""enrich_and_sort.py

Reads a CSV with a 'username' column (e.g. output/not_following_back.csv),
fetches follower counts via Instaloader, and writes a new CSV sorted by
follower count descending.

Supports session reuse, resumption on interruption, and optional login for
private accounts.

Usage:
    # Public profiles only (no login)
    python enrich_and_sort.py --input output/not_following_back.csv

    # With login (required to see follower counts on private accounts)
    python enrich_and_sort.py --input output/not_following_back.csv --login

    # Resume a previous interrupted run
    python enrich_and_sort.py --input output/not_following_back.csv --resume

Options:
    --input         Path to input CSV  (required)
    --output        Path to output CSV  (default: output/not_following_back_sorted.csv)
    --login         Prompt for Instagram credentials and save session
    --session-file  Custom session file path
    --delay         Seconds to wait between API requests  (default: 2.5)
    --resume        Skip usernames already present in output file
"""

import csv
import argparse
import time
import sys
import getpass
from pathlib import Path
from datetime import datetime

try:
    import instaloader
except ImportError:
    instaloader = None


# ──────────────────────────────────────────────────────────────────────────────
# I/O helpers
# ──────────────────────────────────────────────────────────────────────────────

def read_usernames(path: Path):
    users = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        col = None
        if reader.fieldnames:
            for candidate in ("username", "user", "handle"):
                if candidate in reader.fieldnames:
                    col = candidate
                    break
            if col is None:
                col = reader.fieldnames[0]
        for row in reader:
            u = row.get(col, "").strip().lower()
            if u:
                users.append(u)
    return users


def load_done(path: Path):
    """Load already-processed usernames from a partial output CSV."""
    done = {}
    if not path.exists():
        return done
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uname = (row.get("username") or "").strip().lower()
            if not uname:
                continue
            val = row.get("followers", "")
            try:
                done[uname] = int(str(val).replace(",", "")) if val not in ("", "N/A", None) else None
            except (ValueError, TypeError):
                done[uname] = None
    return done


def save_csv(path: Path, rows):
    """Write sorted results to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "followers", "profile_link"])
        for username, followers in rows:
            writer.writerow([
                username,
                followers if followers is not None else "N/A",
                f"https://www.instagram.com/{username}/",
            ])


# ──────────────────────────────────────────────────────────────────────────────
# Instaloader session setup
# ──────────────────────────────────────────────────────────────────────────────

def setup_loader(login: bool, session_file_arg):
    if instaloader is None:
        print("❌  instaloader not found. Install it with:  pip install instaloader", file=sys.stderr)
        sys.exit(1)

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        quiet=True,
    )

    if not login:
        return L

    insta_user = input("Instagram username (for session login): ").strip()
    session_path = Path(session_file_arg) if session_file_arg else Path("sessions") / f"{insta_user}.session"

    if session_path.exists():
        try:
            L.load_session_from_file(insta_user, filename=str(session_path))
            print(f"✅  Loaded existing session from {session_path}")
            return L
        except Exception as e:
            print(f"⚠️  Could not load session ({e}), logging in fresh ...")

    password = getpass.getpass("Instagram password: ")
    try:
        L.login(insta_user, password)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        L.save_session_to_file(filename=str(session_path))
        print(f"✅  Session saved to {session_path}")
    except Exception as e:
        print(f"⚠️  Login failed: {e}. Continuing without authentication.")

    return L


# ──────────────────────────────────────────────────────────────────────────────
# Fetcher
# ──────────────────────────────────────────────────────────────────────────────

def fetch_follower_count(L, username: str):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        return getattr(profile, "followers", None)
    except instaloader.exceptions.ProfileNotExistsException:
        return None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Enrich a username CSV with Instagram follower counts, sorted descending.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python enrich_and_sort.py --input output/not_following_back.csv
  python enrich_and_sort.py --input output/not_following_back.csv --login --resume
        """,
    )
    parser.add_argument("--input",   "-i", required=True,
                        help="Input CSV path (must contain a 'username' column)")
    parser.add_argument("--output",  "-o", default="output/not_following_back_sorted.csv",
                        help="Output CSV path  (default: output/not_following_back_sorted.csv)")
    parser.add_argument("--login",          action="store_true",
                        help="Login to Instagram to see follower counts for private accounts")
    parser.add_argument("--session-file",   default=None,
                        help="Path to save/load Instaloader session  (default: sessions/<user>.session)")
    parser.add_argument("--delay",          type=float, default=2.5,
                        help="Delay between requests in seconds  (default: 2.5)")
    parser.add_argument("--resume",         action="store_true",
                        help="Resume from an existing partial output file")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"❌  Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    L    = setup_loader(args.login, args.session_file)
    users = read_usernames(input_path)
    print(f"\n📋  Loaded {len(users)} usernames from {input_path}")

    done = {}
    if args.resume:
        done = load_done(output_path)
        if done:
            print(f"🔄  Resuming: {len(done)} usernames already cached from {output_path}")

    results = []
    total   = len(users)
    start   = datetime.now()

    for idx, username in enumerate(users, start=1):
        if username in done:
            results.append((username, done[username]))
            print(f"  [{idx:>{len(str(total))}}/{total}]  {username:<30}  (cached)  {done[username] or 'N/A'}")
            continue

        count = fetch_follower_count(L, username)
        results.append((username, count))
        label = f"{count:,}" if count is not None else "private/not found"
        print(f"  [{idx:>{len(str(total))}}/{total}]  {username:<30}  {label}")

        # Auto-save every 20 fetches to protect against interruption
        if idx % 20 == 0:
            partial = sorted(results, key=lambda x: x[1] or 0, reverse=True)
            save_csv(output_path, partial)
            elapsed = (datetime.now() - start).seconds
            print(f"    💾  Auto-saved {len(results)} results  ({elapsed}s elapsed)")

        time.sleep(args.delay)

    sorted_results = sorted(results, key=lambda x: x[1] or 0, reverse=True)
    save_csv(output_path, sorted_results)

    elapsed = (datetime.now() - start).seconds
    fetched = sum(1 for u in users if u not in done)
    print(f"\n✅  Done! {fetched} profiles fetched in {elapsed}s.")
    print(f"   Sorted results saved to: {output_path.resolve()}\n")


if __name__ == "__main__":
    main()
