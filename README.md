# random-github-status

![Status Automation](https://github.com/4uffin/random-github-status/actions/workflows/main.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)
![GitHub repo size](https://img.shields.io/github/repo-size/4uffin/random-github-status?label=Repository%20Size&color=%23FFA500)

A minimalist automation engine that keeps my GitHub profile active by rotating through a pool of 200+ tech-centric, retro, and gaming-inspired statuses hourly.

### 🧠 The Logic
* **0% Repetition:** Uses `last_status.txt` to ensure the same status is never chosen twice in a row.
* **Resilient:** Equipped with exponential backoff and 3x retries to survive network flakiness.
* **Stat Tracking:** Logged in `stats.json` for real-time debugging and error rate calculation.
* **Atomic:** Prevents merge conflicts via `git rebase` logic within the runner.

### 📊 Vital Signs
Current performance metrics can be found in **[stats.json](./stats.json)**.

| Metric | Description |
| :--- | :--- |
| **Total Attempts** | Every execution of the hourly CRON. |
| **Error Rate** | Success vs. Failure percentage for API calls. |
| **Last Run** | The last successful status synchronization. |

### 🛠️ Manual Setup
1.  **Fork** the repository.
2.  **Generate a PAT** ([Personal Access Token](https://github.com/settings/tokens)) with `user` scope.
3.  **Add Secret** to your repo: `Settings > Secrets > Actions > STATUS_TOKEN`.
4.  **Enable Actions** and let the CRON take over.

### 🤝 Pull Requests
Got a status idea? Add your `("Message", ":emoji:")` pair to the pool in `update_status.py` and open a PR. 

### 🧪 Origins
Vibe-coded via **Google Gemini 3 Fast**. No centralized databases, no bloat, just Python and GitHub Actions.
