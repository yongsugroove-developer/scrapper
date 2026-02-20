# scrapper

Daily crawler + summarizer + email digest for the keyword:
`sh 공사 마곡 분양`

This MVP collects broad web results, extracts article text, ranks relevance,
summarizes with OpenAI, and emails one daily digest at 08:00 Asia/Seoul.

## Features (MVP)
- Broad keyword-based web search (no fixed target domain)
- Related-keyword expansion and relevance scoring
- 7-day dedupe by URL + similar title
- Detailed summaries using OpenAI API
- Email delivery via SMTP (free baseline: Gmail SMTP)
- Local persistence with SQLite
- Windows Task Scheduler scripts for daily 08:00 run

## Project Structure
- `scrapper/` application code
- `scripts/` local run and schedule scripts
- `docs/decision-log.md` confirmed decisions

## 1) Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then set:
- `OPENAI_API_KEY`
- `RECIPIENT_EMAIL`
- `SMTP_USERNAME`
- `SMTP_APP_PASSWORD`
- optional `SENDER_EMAIL` (default = SMTP_USERNAME)

For Gmail SMTP, use an app password.

## 2) Dry Run
```powershell
.\scripts\run_daily.ps1 -DryRun
```

## 3) Real Run (send email)
```powershell
.\scripts\run_daily.ps1
```

## 4) Register Daily 08:00 Task (Windows)
```powershell
.\scripts\register_task.ps1
```

Optional:
```powershell
.\scripts\register_task.ps1 -TaskName "ScrapperDailyDigest" -RunAt "08:00"
```

Remove task:
```powershell
.\scripts\unregister_task.ps1
```

## Notes
- Scheduled task time is local machine time. Set Windows timezone to
  `Korea Standard Time` for Asia/Seoul 08:00 behavior.
- When content extraction fails, digest still includes title/link and
  summary fallback text.
- `data/scrapper.db` stores sent history for dedupe.

