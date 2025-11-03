#!/usr/bin/env python3
"""enrich_and_sort.py

Reads an input CSV with 'username' column (default: output/not_following_back.csv),
fetches follower counts using Instaloader, and writes a sorted CSV (descending followers).

Usage:
    python enrich_and_sort.py --input output/not_following_back.csv --output output/not_following_back_sorted.csv
Options:
    --login : prompt for Instagram username + password to use a logged-in session (needed to see private accounts you follow)
    --session-file : path to save/load instaloader session (default: sessions/<insta_username>.session)
    --delay : seconds to wait between requests (default: 2)
    --resume : if output file exists, resume from where left off
"""
import csv
import argparse
import time
from pathlib import Path
import getpass

try:
    import instaloader
except Exception:
    instaloader = None

def read_usernames_from_csv(path: Path):
    users = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "username" not in reader.fieldnames:
            f.seek(0)
            reader2 = csv.reader(f)
            next(reader2, None)
            for row in reader2:
                if row:
                    users.append(row[0].strip().lower())
            return users
        for row in reader:
            u = row.get("username") or row.get("user") or list(row.values())[0]
            if u:
                users.append(u.strip().lower())
    return users

def save_results_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["username", "followers", "profile_link"])
        for u, followers in rows:
            w.writerow([u, followers if followers is not None else "N/A", f"https://instagram.com/{u}"])

def main():
    parser = argparse.ArgumentParser(description="Enrich usernames with follower counts using Instaloader.")
    parser.add_argument("--input", "-i", required=True, help="Input CSV path (must have 'username' column).")
    parser.add_argument("--output", "-o", default="output/not_following_back_sorted.csv", help="Output CSV path.")
    parser.add_argument("--login", action="store_true", help="Login to Instagram to access private accounts you follow.")
    parser.add_argument("--session-file", default=None, help="Session file path (optional).")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds).")
    parser.add_argument("--resume", action="store_true", help="Resume if output already exists.")
    args = parser.parse_args()

    if instaloader is None:
        raise SystemExit("Error: instaloader library not found. Run `pip install instaloader` first.")

    L = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False)
    session_file = None
    if args.login:
        insta_user = input("Instagram username for login (for private access): ").strip()
        if args.session_file:
            session_file = Path(args.session_file)
        else:
            session_file = Path("sessions") / f"{insta_user}.session"
        if session_file.exists():
            try:
                L.load_session_from_file(insta_user, filename=str(session_file))
                print(f"Loaded session from {session_file}")
            except Exception as e:
                print("Couldn't load session:", e)
                passwd = getpass.getpass("Instagram password: ")
                try:
                    L.login(insta_user, passwd)
                    session_file.parent.mkdir(parents=True, exist_ok=True)
                    L.save_session_to_file(filename=str(session_file))
                    print("Saved session to", session_file)
                except Exception as ex:
                    print("Login failed:", ex)
        else:
            passwd = getpass.getpass("Instagram password: ")
            try:
                L.login(insta_user, passwd)
                session_file.parent.mkdir(parents=True, exist_ok=True)
                L.save_session_to_file(filename=str(session_file))
                print("Saved session to", session_file)
            except Exception as ex:
                print("Login failed:", ex)

    input_path = Path(args.input)
    output_path = Path(args.output)

    users = read_usernames_from_csv(input_path)
    print(f"Loaded {len(users)} usernames from {input_path}")

    done = {}
    if args.resume and output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                uname = row.get("username")
                if uname:
                    val = row.get("followers")
                    try:
                        valnum = int(val.replace(",", "")) if val not in (None, "", "N/A") else None
                    except Exception:
                        valnum = None
                    done[uname.lower()] = valnum
        print(f"Resuming: found {len(done)} already-fetched users in {output_path}")

    results = []
    total = len(users)
    for idx, u in enumerate(users, start=1):
        if u in done:
            results.append((u, done[u]))
            print(f"[{idx}/{total}] {u} → (cached) {done[u]}")
            continue
        print(f"[{idx}/{total}] Fetching {u} ...")
        followers_count = None
        try:
            profile = instaloader.Profile.from_username(L.context, u)
            followers_count = getattr(profile, "followers", None)
        except Exception as e:
            print(f"  warning: couldn't fetch {u}: {e}")
            followers_count = None
        results.append((u, followers_count))
        if idx % 20 == 0:
            tmp_sorted = sorted(results, key=lambda x: x[1] or 0, reverse=True)
            save_results_csv(output_path, tmp_sorted)
            print(f"  partial results saved to {output_path} (after {idx} users)")
        time.sleep(args.delay)

    sorted_results = sorted(results, key=lambda x: x[1] or 0, reverse=True)
    save_results_csv(output_path, sorted_results)
    print("✅ Done. Saved sorted results to", output_path)

if __name__ == "__main__":
    main()
