# Deploying to a server

Runbook for the internal deployment (interns + internal presentation), using
Docker Compose on a single host. Every command here has been run against the
real image.

---

## 1. Prerequisites

On the server:

- **Docker Engine 24+** with the Compose plugin (`docker compose version`)
- **~8 GB free disk** — 2.1 GB image, plus Postgres, Qdrant and their volumes
- **4 GB RAM minimum.** Embeddings run on CPU inside the API container
- **Port 8000** reachable by the people who will use it
- **A reachable LLM endpoint** (vLLM, OpenAI-compatible)

That last one is not optional. Without it the service starts and answers
`/health`, but every `/chat` call returns `502`.

**Test it from the server itself, not from your laptop.** This has bitten us:
an endpoint reachable from a workstation was not reachable from the deployment
host, because the LLM host allowlists source IPs. The symptom is TCP connecting
while the TLS handshake never completes — `curl` sends its ClientHello and then
hangs until timeout, rather than failing fast.

```bash
ssh <user>@<server>
curl -sS --max-time 20 <OPENAI_BASE_URL>/v1/models -H "Authorization: Bearer <key>"
```

If that hangs, the deployment host needs allowlisting on the LLM side — no
amount of config here will fix it.

**Split-horizon DNS.** If the LLM is addressed by hostname, check the server can
resolve it. An internal resolver that is authoritative for the company zone but
has no record for the LLM host returns NXDOMAIN rather than forwarding, so the
name fails inside the container even though the internet works. The API service
sets `dns: 1.1.1.1` for this reason; override with `DOCKER_DNS` if your network
needs an internal resolver instead. Using a bare IP in `OPENAI_BASE_URL` avoids
the issue entirely.

Postgres and Qdrant are **not** prerequisites — Compose runs them for you.

---

## 2. Get the code

```bash
git clone git@github.com:yahia-abourgailah/onboard-agent.git
cd onboard-agent
git checkout main
```

`main`, `staging` and `dev` are currently identical, so `main` is right for a
demo deployment.

---

## 3. Generate an API token

```bash
python3 token_generator.py
# sk_xTf9…
```

Keep it. Every client needs it as `Authorization: Bearer <token>`, and the
frontend team needs it too (see `docs/frontend-integration.md`).

---

## 4. Write the `.env`

```bash
cp .env.example .env
```

Then edit it. Four values must be set — Compose **refuses to start** without
them, deliberately, so a missing secret stops the deploy rather than producing
a service that rejects every request:

```ini
API_TOKEN=sk_xTf9…                          # from step 3
POSTGRES_PASSWORD=<a long random string>    # you choose; nothing else reads it
OPENAI_BASE_URL=http://<vllm-host>:8000/v1  # your LLM endpoint
PUBLIC_API_BASE_URL=http://<server-ip>:8000 # what the BROWSER can reach
```

And one you'll want as soon as there's a frontend:

```ini
CORS_ALLOW_ORIGINS=["http://<frontend-host>"]
```

Notes that cost real debugging time:

- **`PUBLIC_API_BASE_URL` must be browser-reachable.** It is baked into the
  floor-map URLs the API returns. Left at `localhost:8000`, map images break
  for everyone except someone browsing on the server itself.
- **`CORS_ALLOW_ORIGINS` cannot be `["*"]`.** The API uses cookies, so it runs
  with credentialed CORS, and browsers reject a wildcard with credentials. List
  exact origins.
- **Do not set `POSTGRES_URL`.** Compose builds it from `POSTGRES_PASSWORD`.
  Setting both gets you two different passwords and a connection failure.
- **Do not set `ALLOW_UNAUTHENTICATED`.** Compose runs `ENVIRONMENT=production`,
  where it has no effect anyway — but leaving it out keeps the intent clear.

`.env` is gitignored. Never commit it.

---

## 5. Build and start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First build takes roughly 5–10 minutes: it installs CPU-only PyTorch and bakes
the embedding model into the image so the container never needs internet at
runtime.

**On a disk-constrained host, transfer the image instead of building it.** The
build needs roughly 6–8 GB transient for the build cache, against a 2.1 GB
final image. With less than ~10 GB free, build on a workstation and ship it:

```bash
# on your machine
docker build -t onboard-agent:latest .
docker save onboard-agent:latest | gzip -1 | ssh <user>@<server> 'gunzip | docker load'

# on the server — no --build, so Compose uses the loaded image
docker compose -f docker-compose.prod.yml up -d
```

**First startup is slow — 1 to 3 minutes.** Before serving traffic the app
seeds the directory database, creates the checkpointer tables, and — if the
Qdrant collection does not exist yet — loads every PDF in `data/`, chunks it,
and embeds it. Subsequent restarts reuse the collection and take seconds.

Watch it come up:

```bash
docker compose -f docker-compose.prod.yml logs -f api
```

Wait for `Application startup complete.`

---

## 6. Verify

```bash
TOKEN=<your API_TOKEN>

curl -s http://localhost:8000/health
# {"status":"ok"}

curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' -d '{"prompt":"hi"}'
# 401  <- auth is on

curl -s -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"what floor is HR on?"}'
# {"response":"HR is on the first floor…","floor_map":{…}}

curl -s -o /dev/null -w '%{http_code}\n' 'http://localhost:8000/floor-map?highlight=hr'
# 200
```

If the third command returns `502`, the app is healthy but cannot reach the
LLM — check `OPENAI_BASE_URL` from *inside* the container:

```bash
docker compose -f docker-compose.prod.yml exec api \
  python -c "import os,urllib.request; print(urllib.request.urlopen(os.environ['OPENAI_BASE_URL']+'/models').status)"
```

Finally, confirm no credential is being logged:

```bash
docker compose -f docker-compose.prod.yml logs api | grep -c "$TOKEN"
# 0
```

---

## 7. Day-to-day

```bash
# logs
docker compose -f docker-compose.prod.yml logs -f api

# restart just the API
docker compose -f docker-compose.prod.yml restart api

# stop everything (volumes survive)
docker compose -f docker-compose.prod.yml down

# deploy a new version
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

`down` keeps the Postgres and Qdrant volumes. **`down -v` deletes them** —
every conversation and the vector index, forcing a full re-ingest on next
start. Only use it when you want that.

To re-ingest after changing the PDFs in `data/`, drop the collection so the
app rebuilds it on next start. Run this through the **api** container — the
Qdrant image ships no shell tooling (`curl` is not installed), and Qdrant's
port is deliberately not published to the host:

```bash
docker compose -f docker-compose.prod.yml exec api python -c \
  "from qdrant_client import QdrantClient; \
   QdrantClient(url='http://qdrant:6333').delete_collection('onboarding_kb')"

docker compose -f docker-compose.prod.yml up -d --build   # rebuild to pick up new PDFs
```

Rebuild rather than restart: the PDFs are copied into the image at build time,
so a plain `restart` re-ingests the *old* documents. Expect the slow first-boot
again while it re-embeds.

To check what is currently indexed:

```bash
docker compose -f docker-compose.prod.yml exec api python -c \
  "from qdrant_client import QdrantClient; \
   print(QdrantClient(url='http://qdrant:6333').get_collection('onboarding_kb').points_count)"
```

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `required variable API_TOKEN is missing` | `.env` missing or incomplete | Step 4 |
| Startup dies after ~30s, `PoolTimeout` | Postgres not reachable | `docker compose -f docker-compose.prod.yml ps` — Postgres should be `healthy` |
| `500 API_TOKEN is not configured` | Container started without the token | Recreate: `up -d --force-recreate api` |
| All `/chat` return `502` | LLM unreachable | Check `OPENAI_BASE_URL` (step 6) |
| LLM curl hangs, TCP port is open | Server not allowlisted on the LLM host | Infra must permit the server's IP; not fixable here |
| LLM host won't resolve in container | Split-horizon DNS | Use an IP in `OPENAI_BASE_URL`, or set `DOCKER_DNS` |
| Browser: CORS error | Origin not allow-listed | Add it to `CORS_ALLOW_ORIGINS`, recreate |
| Map images 404 in browser | `PUBLIC_API_BASE_URL` not browser-reachable | Set it to the server's real address |
| `429` responses | Rate limit (20 req/min per token+session) | Raise `RATE_LIMIT_MAX_REQUESTS` |
| Agent says it has no directions for Sales | Expected — see below | — |

---

## 9. Known limits of this deployment

Deliberate tradeoffs for an internal demo. Worth knowing before the
presentation so nothing is a surprise on the day.

- **One worker.** The rate limiter counts in process memory, so multiple
  workers would allow a multiple of the configured limit. Fine for demo load;
  needs shared state (Redis) before scaling out.
- **One shared API token, no per-user identity.** Anyone with the token can
  use the API, and `thread_id` is a client-supplied cookie — nothing binds a
  conversation to a person. Do not use this with real personal data.
- **Cookies are not marked `Secure`/`SameSite`.** If you put this behind HTTPS,
  session cookies still work but aren't hardened. Fix before external exposure.
- **`/health` does not check dependencies.** It returns `ok` if the process is
  alive. In practice startup is eager — the app fails to boot at all if
  Postgres or Qdrant is down — so a running container does imply working
  dependencies. It would not catch a dependency dying *later*.
- **The floor map covers the first floor only.** No entries for Sales,
  Marketing, Sales Operations or Business Relations, so the agent will say it
  has no directions for those. Sales spans floors two to six, so this is likely
  to come up — worth steering demo questions toward HR, Tech, Finance or IT.
- **No HTTPS.** Terminate TLS at a reverse proxy (nginx/Caddy) if this leaves
  the internal network.

---

## 10. CI/CD

`.github/workflows/deploy.yml` maps branches to environments but its deploy
step is still a placeholder that echoes a TODO — it does not deploy anything.
This runbook is the actual path today. Wiring CI to it means building and
pushing the image to a registry and having the server pull, which needs a
registry and a deploy credential that don't exist yet.
