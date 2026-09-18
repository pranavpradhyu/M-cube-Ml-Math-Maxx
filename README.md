# M³ — ML Math Maxx

🌐 **Live app:** https://m-cube-ml-math-maxx.onrender.com

A community platform for learning the **mathematics behind machine learning**, built with
Flask. Modules, chapters and problems are seeded from *Mathematics for Machine Learning*
(Deisenroth, Faisal & Ong, 2020) and can be extended by any user. Problems use free-text
answers (no MCQs), each with a difficulty level, a **locked editorial**, and a per-problem
**discussion**.

## Features
- **Animated M³ login** — a vibrating brain bursting with formulas, then the form reveals.
- **1000 problems per module** — every module is seeded with ~1000 auto-generated, **answer-checkable**
  practice problems spread across its topics and Easy/Medium/Hard tiers, plus curated worked examples.
  Users can add their own modules, chapters and problems too.
- **Auto-verified solutions** — type an answer; a correct one shows a green “verified” message and marks
  the problem **complete**. Until then it stays **incomplete** (the old manual “mark complete” is gone).
  You can delete your own posted answers.
- **Streak points & medals**
  - +1 point for **logging in each day**
  - +10 points the first time you **solve a problem correctly**
  - −10 points to **unlock a problem’s editorial** (editorials are locked by default)
  - Medals: 🥈 Silver (1000) · 🥇 Gold (5000) · 💎 Platinum (10000)
- **Community feed** (left of dashboard) — post text and **attach files** (images, PDF, DOCX, etc.)
  visible to everyone. **Edit** and **delete** your own posts. Adding a module/chapter/problem auto-posts a link.
- **Per-problem discussion** with image upload; edit or delete your own messages. **Editorial** with a step-by-step solution (locked).
- **Delete a module** — removes all its chapters, problems, submissions, discussions and related posts.
- **Number Game** — timed mental arithmetic; pick a time from a **1–60 second** dropdown and see the
  **global best** and **your best** for the chosen difficulty + time.
- **Profile** — top-right dropdown with logout; editable name, photo and email; points, medals, problems solved.
- **Notifications** — bell icon (in-app) plus **optional email** on new posts, discussion replies and feedback replies.
- **Light / dark toggle**, and a **mobile-responsive** layout.

## Run locally (for development — the public link above is the one to share)
```bash
cd mathmaxx
python -m venv venv
# Windows PowerShell: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# Windows PowerShell:  $env:SECRET_KEY="something-random"
# macOS/Linux:         export SECRET_KEY="something-random"
python app.py
```
Open the address shown in the terminal (Flask's default local dev server) in your browser —
this only works on your own machine, never for anyone else. Register, and you're in. First run
creates the database and seeds the curriculum + ~11,000 practice problems automatically (a second
or two).

> **Upgrading from an older M³ build?** The database schema changed again (discussion messages now
> track an `edited` flag). Delete the old `mathmaxx.db` once before starting so the new column is
> created: `del mathmaxx.db` (Windows) / `rm mathmaxx.db` (macOS/Linux). This wipes local data — on
> Render, this only matters if you're using persistent Postgres; ephemeral SQLite resets on its own.

## Email notifications (optional)
In-app bell notifications always work. To also send **email**, set these environment variables before
starting (e.g. a Gmail App Password): `SMTP_HOST`, `SMTP_PORT` (587 STARTTLS or 465 SSL), `SMTP_USER`,
`SMTP_PASS`, and optionally `MAIL_FROM` and `APP_BASE_URL`. If unset, email is skipped silently.

## Deploy (already live on Render)
This app is deployed at https://m-cube-ml-math-maxx.onrender.com via a Render **Web Service**
connected to this GitHub repo (`render.yaml` + `Procfile` define the build/start commands). Render
**auto-deploys**: any `git push` to the connected branch triggers a fresh build automatically — no
manual redeploy step needed. `SECRET_KEY` is set on Render's dashboard (Environment tab), not in code.

On the free tier, the SQLite database and any uploaded files (photos, PDFs, post attachments) sit on
ephemeral disk and reset on every redeploy/restart. For data that survives restarts, add a Render
**PostgreSQL** instance and set `DATABASE_URL` on the web service to the connection string it gives you
— the app auto-detects and uses it.

## Notes on the problem bank & verification
The 1000/module problems are **parametrized, auto-generated** instances (randomised numbers with computed
answers) themed to each module's topics — that's what makes them auto-gradable at that volume. Answer
checking normalises whitespace/case and compares numerically when possible. Conceptual curated problems
without a stored answer accept a written solution without auto-grading.

## Module / point choices worth knowing
- A problem is **complete** only after a verified-correct answer.
- Anyone can delete a module (with a confirm dialog) — there's no admin role; suitable for a small
  trusted community. Add role checks if you open it up widely.

## Project layout
```
mathmaxx/
├── app.py              # routes
├── models.py           # database models
├── seed_content.py     # curriculum + bulk problem seeding
├── problem_bank.py     # parametrized problem generator (answer-checkable)
├── number_game.py      # number-game question generator
├── notifications.py    # in-app + optional email notifications
├── templates/  ·  static/css/style.css  ·  static/uploads/
├── requirements.txt · Procfile · render.yaml
```
