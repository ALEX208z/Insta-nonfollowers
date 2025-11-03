# insta-nonfollowers

Tools to compare your Instagram followers/following exported JSONs, and to enrich/sort a CSV of usernames by follower count.

## Contents
- `compare_insta_json.py` — parse Instagram export JSON files (`followers_1.json`, `following.json`) and produce CSVs:
  - `output/not_following_back.csv`
  - `output/followers_only.csv`
  - `output/mutuals.csv`
- `enrich_and_sort.py` — read a CSV of usernames and fetch follower counts using Instaloader, then produce a sorted CSV.
- `run_all.py` — end-to-end runner that calls the other two scripts.
- `requirements.txt`, `.gitignore`, `LICENSE`.

## Quick start (local)
1. Place your `followers_1.json` and `following.json` in the project root (or pass paths to scripts).
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate    # Windows PowerShell
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage examples

### 1) Parse JSONs -> CSVs
```bash
python compare_insta_json.py --followers followers_1.json --following following.json
```

### 2) Enrich & sort (public profiles only)
```bash
python enrich_and_sort.py --input output/not_following_back.csv --output output/not_following_back_sorted.csv
```

### 3) Enrich & sort (with login — recommended to access private accounts you follow)
```bash
python enrich_and_sort.py --input output/not_following_back.csv --output output/not_following_back_sorted.csv --login
```

### 4) Full pipeline (end-to-end)
Prompt for login (recommended):
```bash
python run_all.py --login
```
Skip login (faster, public profiles only):
```bash
python run_all.py
```

## Notes & privacy
- Keep your JSON exports and session files private.
- Session files (saved when using `--login`) are stored under `sessions/` by default. `.gitignore` excludes these.
- Do not commit `output/` or `sessions/` to a public repository.

## License
MIT
