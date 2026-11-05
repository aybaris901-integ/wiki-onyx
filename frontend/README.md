# Company Brain frontend

Next.js 16, no sign-in. The landing page is at `/` and the chat is at `/app`.

## Run it

```
npm install
npm run dev
```

Without any settings it runs on stand-in answers, and each one is stamped "Sample answer" on the page.

## Connect the real agent

Put the agent's base address in `.env.local` and restart the dev server:

```
ASK_BACKEND_URL=http://localhost:8000
```

The browser only talks to this app's `/api/ask`, which forwards to the agent on the server, so the agent doesn't need CORS.

## What it sends the agent

`POST {ASK_BACKEND_URL}/ask` with `{ "question": "..." }`

## What it expects back

```json
{
  "answer": "One or two plain sentences.",
  "sources": [
    {
      "type": "pr",
      "url": "https://github.com/org/repo/pull/482",
      "author": "Maya Okafor",
      "date": "2025-11-19"
    }
  ]
}
```

`type` picks the card. Use one of:

| type | Card label | Card color |
|---|---|---|
| `slack` | Discussed in | green |
| `pr` | Written in | blue |
| `commit` | Changed in | blue |
| `code` | Lives in (a link's last part shows as the file name) | black |
| `doc` | Written down in | light blue |
| `owner` | Owned by (`author` is the owner) | red |

Anything else still shows as a plain source card.

Optional on any source, and worth sending:

- `title`: the PR or document title
- `quote`: the exact line that backs the answer, shown in quotes on the card

Empty `sources` tells the reader to check with a person before acting on the answer.

Return 429 when rate limited. Any other error status shows "The answer service isn't responding". The page waits 30 seconds for the agent.

## Demo questions

Edit `EXAMPLE_QUESTIONS` in `lib/answer.ts`.
