<div align="center">

# 📸 insta-nonfollowers

**Find out who doesn't follow you back on Instagram — using your own data export, no third-party apps.**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![No login required](https://img.shields.io/badge/login-optional-orange?style=flat-square)](#)

</div>

---

## ✨ What it does

Instagram doesn't tell you who doesn't follow you back. This tool does — **without scraping or third-party access to your account.** You download your own data from Instagram, drop in the JSON files, and run a single command.

| Output file | Contents |
|---|---|
| `not_following_back.csv` | Accounts you follow who don't follow you back |
| `followers_only.csv` | Accounts that follow you, but you don't follow |
| `mutuals.csv` | Mutual followers |
| `not_following_back_sorted.csv` | Non-followers sorted by follower count *(optional, requires Step 2)* |

---

## 🔒 Privacy first

> Your Instagram data never leaves your machine. No tokens, no third-party APIs, no browser extensions.

- ✅ Works entirely offline (Step 1)
- ✅ No Instagram login required for basic usage
- ✅ Session files are `.gitignore`d by default
- ✅ Output CSVs are `.gitignore`d by default

---

## 🚀 Quick start

### 1 — Export your Instagram data

1. Open **Instagram** → **Settings** → **Your activity** → **Download your information**
2. Select **"Connections"** → **Followers and following**
3. Choose format: **JSON**, date range: **All time**
4. Wait for the email from Instagram, then download and unzip the archive

You'll find these files inside:
```
connections/
  followers_and_following/
    followers_1.json
    following.json
```

Place them anywhere accessible (project root is fine).

---

### 2 — Set up the project

```bash
# Clone / download the repo
git clone https://github.com/yourusername/insta-nonfollowers.git
cd insta-nonfollowers

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

---

### 3 — Run

**Simplest — auto-detects your JSON files:**
```bash
python run_all.py
```

**With follower-count enrichment** *(ranks non-followers by how popular they are)*:
```bash
python run_all.py --enrich
```

**With login** *(needed to see follower counts for private accounts you follow)*:
```bash
python run_all.py --enrich --login
```

That's it. Check the `output/` folder for your CSVs.

---

## 🛠 Individual scripts

You can also run each step independently.

### Step 1 — Parse JSON exports → CSV

```bash
python compare_insta_json.py \
  --followers followers_1.json \
  --following following.json
```

Sample output:
```
📂  Loading followers_1.json ...
📂  Loading following.json ...

──────────────────────────────────────────────────────
  📊  Instagram Follower Analysis
  Generated:             2025-06-01  14:22
──────────────────────────────────────────────────────
  You follow:                        842
  Follow you:                        619
──────────────────────────────────────────────────────
  ✅  Mutuals:                        501  → mutuals.csv
  ❌  Not following back:             341  → not_following_back.csv
  👀  You don't follow back:          118  → followers_only.csv
──────────────────────────────────────────────────────
  Mutual rate:                      59.5%
  Output folder:                    /path/to/output
──────────────────────────────────────────────────────
```

### Step 2 — Enrich with follower counts *(optional)*

Uses [Instaloader](https://instaloader.github.io/) to fetch follower counts and sort the list descending — useful for identifying big accounts that aren't following back.

```bash
# Public profiles only (no credentials)
python enrich_and_sort.py --input output/not_following_back.csv

# With login (recommended — allows private account lookup)
python enrich_and_sort.py --input output/not_following_back.csv --login

# Resume an interrupted run
python enrich_and_sort.py --input output/not_following_back.csv --resume
```

> **Tip:** Use `--delay 3` or higher if you have a large list. The default 2.5-second delay is conservative, but Instagram may rate-limit aggressive requests.

---

## 📁 Project structure

```
insta-nonfollowers/
├── compare_insta_json.py      # Step 1: JSON → CSV parser
├── enrich_and_sort.py         # Step 2: follower count enrichment
├── run_all.py                 # Full pipeline runner
├── requirements.txt
├── sample_data/
│   ├── followers_1.json       # Example followers export
│   └── following.json         # Example following export
├── output/                    # Generated CSVs (gitignored)
└── sessions/                  # Instaloader sessions (gitignored)
```

---

## ⚙️ CLI reference

### `run_all.py`

| Flag | Description | Default |
|---|---|---|
| `--followers` | Path to followers JSON | Auto-detected |
| `--following` | Path to following JSON | Auto-detected |
| `--outdir` | Output directory | `output/` |
| `--enrich` | Also run Step 2 (fetch follower counts) | `false` |
| `--login` | Login to Instagram during enrichment | `false` |
| `--delay` | Seconds between requests | `2.5` |
| `--resume` | Resume partial enrichment | `false` |

### `compare_insta_json.py`

| Flag | Short | Description |
|---|---|---|
| `--followers` | `-f` | Path to `followers_1.json` |
| `--following` | `-g` | Path to `following.json` |
| `--outdir` | `-o` | Output directory (default: `output/`) |

### `enrich_and_sort.py`

| Flag | Short | Description |
|---|---|---|
| `--input` | `-i` | Input CSV path |
| `--output` | `-o` | Output CSV path |
| `--login` | | Prompt for Instagram credentials |
| `--session-file` | | Custom session file path |
| `--delay` | | Delay between requests (default: `2.5`) |
| `--resume` | | Resume from partial output |

---

## 🧪 Try with sample data

The repo includes sample JSON files to test with:

```bash
python compare_insta_json.py \
  --followers sample_data/followers_1.json \
  --following sample_data/following.json \
  --outdir output/
```

---

## 🐛 Troubleshooting

**"No followers/following found"**
Make sure you're using the JSON format (not HTML) when requesting your data from Instagram. The file should be named `followers_1.json` and contain a top-level array.

**Enrichment is very slow**
That's intentional. Instagram rate-limits requests; the `--delay` flag controls the gap between calls. Use `--resume` to safely interrupt and continue later.

**Private accounts show `N/A` for followers**
You need to use `--login` to authenticate. The tool will save your session locally so you only need to log in once.

**`instaloader` not found**
```bash
pip install instaloader
```

---

## 📝 Notes

- Instagram occasionally changes its export format. If parsing fails, open an issue with a sanitized snippet of your JSON structure.
- Session files let you avoid re-entering credentials each run. They are stored in `sessions/` and excluded from git.
- This tool does not modify your Instagram account in any way.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
  Made with Python · No scraping · No third-party apps · Your data stays yours
</div>
