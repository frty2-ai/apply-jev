# Access: the canonical contract and the known routes

This skill is vendor-neutral. Jev is served by TypeSafe directly and resold or wrapped by
several gateways and frameworks. All of them carry the same *core* contract; some wrap it.
Learn the contract, then read the vendor's page for path, auth and wrapper.

## The canonical request

```json
{
  "model": "jev-1.13.0",
  "state": "string, or a JSON object, or an array of text",
  "questions": {
    "is_urgent": {
      "type": "noul",
      "instructions": "Does `message` convey urgency?",
      "criteria": { "true": "Explicitly time-sensitive", "false": "No urgency expressed" }
    },
    "department": {
      "type": "choice",
      "instructions": "Which team should handle `message`?",
      "criteria": { "billing": "Payments, invoicing, refunds",
                    "technical": "Bugs, outages, integrations",
                    "other": null }
    },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated is the customer in `message`?",
      "criteria": ["Calm, matter-of-fact", "Frustrated but civil", "Very angry, hostile language"]
    }
  }
}
```

Field notes:

- `model`: a versioned id (`jev-1.13.0`) or an alias (`jev-latest`, `jev-preview`). Pin the
  version once thresholds are tuned. Gateways may prefix (`typesafe/jev-1.13`) or
  suffix; follow theirs.
- `state`: string | object | array. Text only. Nested JSON is encouraged; refer to it
  from questions with backticked paths.
- `questions`: a map. Keys are yours and are **not sent to the model**; all meaning must be
  in `instructions` and `criteria`. Each of `instructions`, Choice option descriptions,
  Score levels and Noul `true`/`false` may be a string, object, array, or `null`.
- Choice: `criteria` required, 1–255 options. Score: `criteria` required, 2–10 levels.
  Noul: `criteria` optional.

## The canonical response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "is_urgent":   { "type": "noul",   "noul": 0.95 },
    "department":  { "type": "choice", "choice": "billing",
                     "probabilities": { "billing": 0.88, "technical": 0.12, "other": 0.0 },
                     "confidence": 0.81 },
    "frustration": { "type": "score",  "score": 1.05,
                     "legend": { "0": "Calm, matter-of-fact", "1": "Frustrated but civil", "2": "Very angry, hostile language" },
                     "probabilities": { "0": 0.0, "1": 0.95, "2": 0.05 },
                     "confidence": 0.92 }
  },
  "usage": { "input_tokens": 318, "output_tokens": 34 }
}
```

`model` reports the versioned id that actually answered; log it with every stored
decision. `usage` field names vary by vendor (`input_tokens` vs `inputTokens`; some add
`cost`). Do not depend on one spelling.

## Limits and errors (TypeSafe direct, `jev-1.13`, as of 2026-09-25)

| | |
| --- | --- |
| Context | 64k tokens per request total; 32k for `state` plus the longest single question |
| Options / levels | Choice ≤ 255 options; Score 2–10 levels |
| Input | Text only; English strongest, other languages accepted with lower accuracy |
| Price | $0.042 per million input tokens; output free (gateways price separately) |
| Rate limits | Described as dynamic; a 429 means back off |
| Latency | ~100 ms typical direct; several hundred ms observed through gateways |
| 401 | Bad or missing key |
| 422 | Request failed validation; body names the field |
| 429 | Rate limited; exponential backoff, honour `retry-after` |
| 529 | Overloaded; retry with backoff |

Jev is not fine-tuned per customer. You shape it through `state`, `instructions` and
`criteria` only. TypeSafe states requests are not used for training; check their legal
pages for data handling and zero-retention options if that matters to the user.

## Known routes (verify before relying; this list drifts)

| Route | How the contract appears | Notes |
| --- | --- | --- |
| TypeSafe API | `POST https://api.typesafe.ai/v1/systemone`, bearer key, body exactly as above | Source of truth. `GET /v1/models` lists aliases. |
| TypeSafe SDKs (Python `typesafe_sdk`, JS `@typesafe-ai/sdk`) | `client.system_one(state=…, questions={…})` with `Noul`/`Choice`/`Score` helpers | Retries 429/529 with backoff by default. `base_url` can point at a compatible gateway. |
| OpenRouter | Dedicated "Decisions" endpoint with the same body (model id prefixed `typesafe/…`); also a System One-compatible path for the TypeSafe SDK | Not the chat-completions endpoint; chat SDKs will not work. |
| Requesty | Chat-completions wrapper: the state goes in a user message, questions in `response_format: {type: "questions", …}`; answers come back as JSON in the assistant message | Marked experimental by the vendor. |
| Cloudflare Workers AI | `env.AI.run("typesafe/jev", { state, questions })` | Same body inside the platform's run call. |
| Vercel AI Gateway, Netlify AI Gateway, ZenMux | Listed with a `typesafe/jev-…` id and their own auth | Check each for whether the body is native or wrapped. |
| Pydantic AI | `TypeSafeModel("jev-latest")` as a `DecisionModel`; an output type's fields become the questions, enum/docstrings become criteria | Enforces the 255/10 limits client-side; can sit in front of an LLM via `FallbackModel`. |

When writing code for a user, ask which route they have, read that vendor's current page,
and keep the vendor-specific part (URL, headers, wrapper) in one small function so the
question bundle and thresholds stay portable.

## Practical hygiene

- Keys server-side only. Never in a browser bundle.
- One module or config for questions + thresholds + pinned model id. It is the part
  humans review and the part that changes when the model does.
- Log `model`, the request's question keys, and the full `answers` object with each
  decision so you can re-threshold later without re-running inference.
- Retry 429/529 with exponential backoff; treat 422 as a bug in your request builder.
