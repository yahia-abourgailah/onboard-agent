# Frontend integration guide

How to talk to the onboarding agent API from a browser client: streaming chat
and the floor-map navigation.

Read the four gotchas first. Each one costs an afternoon if you find it the
hard way.

---

## Four things that will bite you

**1. `EventSource` does not work here.** The streaming endpoint is a `POST`,
and the browser `EventSource` API only issues `GET` and cannot set an
`Authorization` header. Use `fetch` with a `ReadableStream` reader instead.
Working code below.

**2. The streaming endpoint does not return floor maps.** `POST /chat` returns
a `floor_map` object when the agent gives directions; `POST /chat/stream` emits
only text tokens and never includes it. If your UI needs to render maps, either
use the non-streaming endpoint, or detect the intent client-side and call
`GET /floor-map` yourself. See [Choosing an endpoint](#choosing-an-endpoint).

**3. Session cookies are `httpOnly`.** The server issues `session_id` and
`thread_id` as `httpOnly` cookies, so your JS cannot read them — and it does
not need to. You must send `credentials: 'include'` on **every** call or each
message starts a brand-new conversation with no memory of the last one.

**4. CORS requires your exact origin.** Because cookies are used, the server
runs with `allow_credentials=True`, which forbids a wildcard origin. Your
origin must be listed in the API's `CORS_ALLOW_ORIGINS` or the browser blocks
the request. Ask the backend team to add it — it is a deploy-time env var:

```
CORS_ALLOW_ORIGINS=["https://onboarding.internal","http://localhost:3000"]
```

---

## Authentication

Every endpoint except `GET /health` and `GET /floor-map` needs a bearer token:

```
Authorization: Bearer <API_TOKEN>
```

> **Security note, please read.** This is a single shared token, not a per-user
> credential. Anything you ship to a browser is readable by anyone who opens
> devtools. For the internal demo this is an accepted tradeoff, but do **not**
> put this token in a public build, and do not treat it as identifying a user.
> If this becomes a real product, proxy the API behind your own backend and
> issue per-user sessions.

Failure modes:

| Status | Meaning | What to do |
|---|---|---|
| `401` | Missing or wrong token | Show a config error; do not retry |
| `429` | Rate limit exceeded | Back off and retry; show "one moment" |
| `502` | Agent failed (LLM/DB down) | Show a friendly failure; retry is fine |
| `500` | Server misconfigured (no `API_TOKEN` set) | Backend problem, not yours |

---

## Choosing an endpoint

| | `POST /chat` | `POST /chat/stream` |
|---|---|---|
| Response | One JSON object | SSE token stream |
| Feels responsive | No — waits for full answer | Yes |
| Returns `floor_map` | **Yes** | **No** |
| Best for | Anything showing maps | Plain text chat |

The pragmatic combination for a demo: **stream the text**, and when the user
asks a "where is X" question, call `GET /floor-map?highlight=<key>` directly to
render the image. Or use `POST /chat` for everything and accept the wait.

---

## Streaming chat

### Request

```
POST /chat/stream
Authorization: Bearer <API_TOKEN>
Content-Type: application/json

{ "prompt": "fein el HR?" }
```

### Response

`Content-Type: text/event-stream`. Each event is a line beginning `data: `
followed by JSON, then a blank line. Three event types:

```
data: {"type":"token","content":"HR "}

data: {"type":"token","content":"is on "}

data: {"type":"done","session_id":"7f3a…","thread_id":"9c21…"}
```

| `type` | Fields | Meaning |
|---|---|---|
| `token` | `content` | Append to the message being rendered |
| `done` | `session_id`, `thread_id` | Stream finished normally |
| `error` | `detail` | Generation failed; stop and show an error |

An `error` event is terminal — no `done` follows it.

### Working client

```js
async function streamChat(prompt, onToken) {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_TOKEN}`,
    },
    credentials: "include", // REQUIRED — carries the conversation cookies
    body: JSON.stringify({ prompt }),
  });

  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Events are separated by a blank line. Keep the trailing partial chunk
    // in the buffer — a network packet can split an event in half.
    const events = buffer.split("\n\n");
    buffer = events.pop();

    for (const event of events) {
      const line = event.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;

      const payload = JSON.parse(line.slice(6));
      if (payload.type === "token") onToken(payload.content);
      else if (payload.type === "error") throw new Error(payload.detail);
      else if (payload.type === "done") return payload; // {session_id, thread_id}
    }
  }
}
```

The buffering matters. Tokens arrive in whatever chunks the network delivers,
and an event can be split across two reads. Parsing each `value` in isolation
will drop or corrupt tokens under real network conditions.

---

## Non-streaming chat

```
POST /chat
Authorization: Bearer <API_TOKEN>
Content-Type: application/json

{ "prompt": "how do I get to HR?" }
```

```jsonc
{
  "response": "HR is on the first floor — walk toward the centre…",
  "session_id": "7f3a…",
  "thread_id": "9c21…",
  "floor_map": {                                  // null unless directions were given
    "type": "floor_map",
    "destination": "hr",
    "url": "http://localhost:8000/floor-map?highlight=hr",
    "route": "Walk toward the center of the floor — HR has two clusters there…"
  }
}
```

When `floor_map` is non-null, render `floor_map.url` as an image alongside the
text. The agent is instructed to describe the route in prose, so you do **not**
need to display `route` separately — it is there if you want a caption.

---

## Floor map

```
GET /floor-map?highlight=<destination>
```

Public — **no bearer token**, deliberately, so a plain `<img src>` works
(an `<img>` tag cannot attach an `Authorization` header).

Returns `image/svg+xml` with `Cache-Control: public, max-age=3600`. The named
section is highlighted; omit `highlight` for the plain floor plan.

```jsx
{floorMap && (
  <img src={floorMap.url} alt={`Route to ${floorMap.destination}`} />
)}
```

### Valid `highlight` values

```
tech          business_dev   hr          hr_marq        hr_operations
it            eclatic        finance     l_and_d        kitchen
elevators     stairs_main    toilets     offices        meeting_rooms
eclatic_meeting_rooms        gates
```

Anything else returns `400` with the valid list in the body. Do not build the
URL from raw user input — use the `url` the API hands you, or one of the keys
above.

> **Coverage limit.** The map currently covers the **first floor only**. There
> are no entries for Sales, Marketing, Sales Operations, or Business Relations,
> so "where is Sales?" will not produce a map even though Sales occupies floors
> two through six. Handle a null `floor_map` gracefully — it is the common case
> for those departments, not an error.

---

## Conversation lifecycle

Memory is keyed on the `thread_id` cookie and persisted server-side, so it
survives restarts. You do not manage it — just keep sending
`credentials: 'include'`.

To start a fresh conversation:

```js
await fetch(`${API_BASE}/new-chat`, {
  method: "POST",
  headers: { Authorization: `Bearer ${API_TOKEN}` },
  credentials: "include",
});
```

This clears both cookies; the next message begins a new thread.

---

## Input guardrail

Messages matching known prompt-injection patterns are refused before reaching
the model. The user gets a normal assistant reply:

> I can't process that message as written. I can help with onboarding questions
> about company policy, floors/departments, or your mentor — try rephrasing
> your question.

This arrives as ordinary `token` events (streaming) or a normal `response`
(non-streaming) — it is **not** an `error` event and not a non-200 status.
Nothing special to handle. The refused message is discarded server-side, so the
conversation stays usable afterwards; the user can simply carry on.

---

## Local development

```bash
cp .env.example .env          # keeps ALLOW_UNAUTHENTICATED=true for local
docker compose up -d          # Qdrant + Postgres
python main.py                # http://localhost:8000
```

Interactive API docs: <http://localhost:8000/docs>

Point your client at `http://localhost:8000` and add your dev origin to
`CORS_ALLOW_ORIGINS` in `.env`.

`PUBLIC_API_BASE_URL` must be the address the **browser** can reach, since it
is baked into the `floor_map.url` the API returns. If it is left at
`localhost:8000` on a shared deployment, map images will break for everyone
except someone browsing on the server itself.
