# Deploy React + FastAPI on Windows

## Deployment endpoints

- Local origin: `http://127.0.0.1:8501`
- Local API health: `http://127.0.0.1:8501/api/health`
- Public URL: `https://agentlab4.dquangminh2003.id.vn`
- Existing tunnel: `vinuni-research-agent-lab4`
- Method: React/Vite static frontend served by FastAPI/Uvicorn, exposed through
  the existing Cloudflare Tunnel

Do not create a new tunnel, hostname, DNS record, CNAME, or route. Do not put
API keys, Telegram credentials, the Cloudflare token, or `.env` contents in
this file or any committed script.

## Architecture

`npm run build` writes the React application to `frontend/dist/`.
`backend/main.py` mounts that directory at `/` and exposes API endpoints under
`/api`. Uvicorn serves both the frontend and backend on the fixed local origin:

```text
Browser -> Cloudflare -> 127.0.0.1:8501
                         |- /api/*  -> FastAPI
                         `- /*      -> frontend/dist
```

## Terminal 1 - React/FastAPI application

The one-command script:

- checks `.env`, backend files, and frontend files;
- creates/activates `.venv` when needed;
- installs Python dependencies when needed;
- runs `npm ci` when needed;
- builds `frontend/dist`;
- starts Uvicorn at `127.0.0.1:8501`.

```powershell
cd <repo>\starter_v0
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

Equivalent manual commands:

```powershell
cd <repo>\starter_v0

cd frontend
npm ci
npm run build
cd ..

.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8501
```

Verify both frontend and backend locally:

```powershell
Invoke-WebRequest http://127.0.0.1:8501 -UseBasicParsing
Invoke-RestMethod http://127.0.0.1:8501/api/health
```

## Terminal 2 - existing Cloudflare Tunnel

Keep the tunnel token outside the repository. Provide it through the current
terminal's `CLOUDFLARE_TUNNEL_TOKEN` environment variable, then run:

```powershell
cloudflared.exe tunnel run --token $env:CLOUDFLARE_TUNNEL_TOKEN
```

The existing route must continue forwarding
`https://agentlab4.dquangminh2003.id.vn` to `http://localhost:8501`. Do not
change DNS or create another route.

Verify from an incognito window or a phone using mobile data:

```text
https://agentlab4.dquangminh2003.id.vn
```

The public API health endpoint is:

```text
https://agentlab4.dquangminh2003.id.vn/api/health
```

## If the public URL returns 502

Check only:

1. Uvicorn is still running on port `8501`.
2. `http://127.0.0.1:8501` works on the host machine.
3. The `cloudflared` process is still running.

The application is available only while the host machine, Uvicorn, and
`cloudflared` are all running.
