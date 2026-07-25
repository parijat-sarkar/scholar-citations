# Auto-updating Google Scholar citation counter

Fetches your exact Google Scholar citation total on a schedule and displays it
on your Squarespace site. You set it up once; after that it refreshes itself.

**How it works:** a GitHub Action runs weekly, calls SerpApi's Google Scholar
Author API (which returns Scholar's real numbers and handles the CAPTCHAs),
and commits the count to `citations.json`. A small snippet on your Squarespace
page reads that file from a CDN and shows the number. Squarespace never talks
to Google Scholar directly, so nothing gets blocked and the page loads fast.

## One-time setup

### 1. Get a SerpApi key
- Sign up at https://serpapi.com (free tier is ~100 searches/month; this uses
  about 4–5).
- Copy your private API key from the SerpApi dashboard.

### 2. Create a GitHub repo
- Make a new **public** repo (public is required for the free jsDelivr CDN).
- Add these three files to it, keeping the folder layout:
  ```
  fetch_citations.py
  .github/workflows/update-citations.yml
  citations.json          <- optional starter file; the Action will create/update it
  ```
- You do NOT need to upload `squarespace-snippet.html` — that goes into
  Squarespace, not the repo.

### 3. Add your secrets to the repo
In the repo: **Settings → Secrets and variables → Actions → New repository secret.**
Add two secrets:
- `SERPAPI_KEY` — your SerpApi key
- `SCHOLAR_ID` — `ElQU3_0AAAAJ` (the `user=` value from your Scholar profile URL)

### 4. Run it once by hand
- Go to the **Actions** tab → **Update Scholar citations** → **Run workflow.**
- When it finishes, confirm `citations.json` now shows your real count.

### 5. Add the snippet to Squarespace
- Open `squarespace-snippet.html`. Change the one marked line:
  ```
  var JSON_URL = "https://cdn.jsdelivr.net/gh/YOUR_GITHUB_USERNAME/YOUR_REPO@main/citations.json";
  ```
  Replace `YOUR_GITHUB_USERNAME` and `YOUR_REPO` with your actual values.
- On your publications page in Squarespace: **Edit → add a Code Block →** paste
  the whole snippet in → Save.

Done. The number updates every Monday automatically. Change the schedule by
editing the `cron` line in the workflow.

## Notes & troubleshooting

- **The count must match Google Scholar exactly** — that's why this uses
  SerpApi rather than a free alternative (Semantic Scholar / OpenAlex report
  different, usually lower, numbers).
- **A run failed?** The script exits without overwriting `citations.json`, so
  your page keeps showing the last good number. Common causes: wrong/expired
  SerpApi key, monthly quota used up, or a mistyped `SCHOLAR_ID`.
- **Number looks stale?** The snippet cache-busts daily; a hard refresh
  (Ctrl/Cmd-Shift-R) forces it. jsDelivr can also lag up to ~24h after a commit.
- **Want more than just the total?** `citations.json` also carries `h_index`
  and `i10_index`, so you can show those with the same approach.
- **Squarespace plan:** Code Blocks require a Business plan or higher. If you're
  on Personal, the alternative is an embedded image badge, which is less clean —
  ask and I can set that up instead.
