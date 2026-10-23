# Operational Result — restart local read-only Quality API after CR-004

User asked whether `run dev` frontend and API required restart after CR-004 implementation.

Frontend: Next dev/HMR is designed to pick source changes; existing process remained alive and `/` and `/quality` returned 200. No frontend restart performed.

API: source Python imports are not hot-reloaded by the launcher, so restart was required. Exact old PID `37364` was already PID-1-owned zombie after TERM (no listener); port 8000 was free. New process PID `116728` started with the same audited command:

```text
/root/soarplus-api/.venv/bin/python /root/run_api_local_ui.py
```

`GRANT_USER_ID` was unset. Listener is exclusively `127.0.0.1:8000`; health 200. Log markers show `[LOCAL-UI]`, `[READONLY-GUARD]` and Uvicorn running, with no startup error/traceback. Canonical/installed launcher SHA256 remains identical (`df5bb1025c44e71afefe52884893439a83d17ecd0403757792c32a3757259492`).

Independent post-restart GETs for known persisted `judge_unavailable` runs returned 200 and preserved literal statuses for eval runs `3b3b92485eb04087aa8541eadd2b3302` and `da7397152061483fb881a554847abafc`. Frontend `/` and `/quality` returned 200; SystemDevAgent was not restarted.
