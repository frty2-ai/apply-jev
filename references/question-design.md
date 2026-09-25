# Designing questions

Every rule here is derived from a documented failure mode of `jev-1.13` (TypeSafe's
"jaggedness" page) or from its published building guide. The failure mode is stated first
so you understand *why* the rule exists and can judge when it applies.

## Failure mode → rule

| The model… | So you… |
| --- | --- |
| Reads literally: answers the question you wrote, not the one you meant | State the exact condition. Put boundary cases in the criteria. Where interpretation is unavoidable, split into two literal questions and combine in code. |
| Cannot count, compute, or interpolate numbers | Count and calculate in code. Ask one question per item, then add up. Never read an exact magnitude off a Score expectation. |
| Reads dates as text, not quantities | Ask for the parts as Choices (month, day, year, weekday, offset) with `none`/`out_of_range` options; assemble and compare in code. |
| Loses accuracy on indirection and double negatives | One hop per question. Name the state field. Avoid "not un-", "unless", "except when". |
| Degrades as unrelated state grows (context rot) | Filter in code first. Send only the fields the questions need. If you cannot filter, ask a relevance Noul first. |
| Can be moved by adversarial text in the state | Bind fact questions to typed fields, not prose. Pair with deterministic checks. Test with injected instructions. |
| Confuses contradictory instructions and criteria | Make criteria an extension of the instruction. A Noul's `true` must describe a yes. |
| Does not guarantee structural invariants across questions | Ask each decision once, one way. Do not expect `P(a) + P(not a) = 1` or Noul ≈ yes/no Choice. Enforce identities in code. |
| Cannot generate | Turn extraction into selection over candidates code found. Give a `none` option. |

## Decompose

Broad questions hide several judgments behind one number. Atomic questions expose them so
you can inspect, tune and combine.

Bad:

```json
{ "is_spam": { "type": "noul", "instructions": "Is `message` spam?" } }
```

Good:

```json
{
  "requests_credentials":      { "type": "noul", "instructions": "Does `message.body` ask the recipient to provide a password or other login credential?" },
  "offers_unexpected_reward":  { "type": "noul", "instructions": "Does `message.body` claim the recipient received an unexpected prize, payment, or reward?" },
  "creates_time_pressure":     { "type": "noul", "instructions": "Does `message.subject` or `message.body` pressure the recipient to act quickly?" },
  "sender_identity_mismatch":  { "type": "noul", "instructions": "Does the organization named in `message.sender.display_name` conflict with the domain in `message.sender.email`?" },
  "disguises_link_destination":{ "type": "noul", "instructions": "Does `message.links[0].text` conceal or misrepresent the destination in `message.links[0].url`?" }
}
```

Then in code: `spam_risk = 0.45*credentials + 0.30*mismatch + 0.25*reward`, with a review
band around your action threshold. Change a weight without re-running inference.

Atomic does not mean trivial. "Which of these five next actions fits the situation" is one
bounded judgment and a fine question. "Is everything about this request correct" is not.

## Write the instruction

- Ask about the idea, not the words a user might use. "Does the user want the chart drawn
  as candles?" beats "Does the message contain 'candles' or 'OHLC'?" The match is on
  meaning.
- Name the field: `` `ticket.messages[0].text` ``. Backticks are the convention TypeSafe
  trains on.
- Prefer the positive form. "Is the customer asking for a refund?" not "Is the customer not
  asking for something other than a refund?"
- One sentence is usually right. When the question needs context, examples, or data from
  your code, use a structured object rather than a long string:

```json
"instructions": {
  "question": "Is the resume for the same person as `potential_duplicate`?",
  "potential_duplicate": { "name": "John Smith", "location": "Oakland, CA", "last_employer": "Acme" },
  "focus": "Compare identity, not suitability."
}
```

## Write the criteria

**Noul** (`criteria` is optional but usually worth it):

```json
"criteria": {
  "true":  { "what": "Asks the recipient to reply with, type, or send a password, PIN, or one-time code",
             "examples": ["Reply with your password", "Send us the 6-digit code you just received"] },
  "false": { "what": "No credential is requested",
             "not_for": "A legitimate instruction to reset a credential",
             "examples": ["Reset your password from the settings page"] }
}
```

The `not_for` line is where you put the borderline case, on the side you want it.

**Choice** (`criteria` required, up to 255 options; `null` when an option needs no
description):

```json
"criteria": {
  "billing": { "what": "Charges, invoices, refunds, subscriptions", "not_for": "Order tracking or account access", "examples": ["I was charged twice"] },
  "orders":  { "what": "Order status, delivery, cancellation, returns", "not_for": "Charges or account access", "examples": ["Where is my package?"] },
  "other":   "Anything that fits none of the above"
}
```

Use the same field names across options so the model can compare them directly. Always
consider an `other` / `none` option: a Choice is relative and will pick *something*.

**Score** (`criteria` is an ordered array, 2 to 10 levels; each level a concrete scene):

```json
"criteria": [
  { "summary": "One change, clearly stated",            "signals": ["A single fix or feature", "No 'also' or 'while I was in there'"] },
  { "summary": "One main change plus a related tweak",  "signals": ["A primary change and one minor adjacent edit"] },
  { "summary": "Several independent changes bundled",   "signals": ["Two or more unrelated fixes", "Changes that could each be their own PR"] }
]
```

Never write levels as bare numbers. "1 to 10" leaves the meaning of 6 to chance.

## Shape the state

- An object with descriptive keys for anything with more than one part. A string only for
  a single passage.
- Put together what the decision must compare: message + policy + record in one state.
- Leave out what no question needs. Every unrelated field costs accuracy and tokens.
- Pre-process non-text into typed fields. A vision model's structured output, an OCR pass,
  a transcript. Jev judges the fields; it never sees the pixels.
- Keep observed facts separate from inferred ones, and mark which is which in the key
  names (`verifier.printed_page_visible` vs `claimant_says`).

## Speculate, then let code choose

Because questions run in parallel over one state, ask everything the workflow might need
in one call. If the ticket is a bug, you will want severity and repro steps; if it is a
billing issue, refund-requested. Ask all of them up front; code reads the branch that
applies and ignores the rest. A second call is warranted only when an answer changes
*which state to fetch* or *which options exist*.

## Escape hatches

A model forced to pick from a closed set will pick. Give it a way to report absence:

- `none` / `not_stated` for extraction-as-selection.
- `other` for classification.
- `out_of_range` when the answer may exist but is not among the options.
- A separate presence Noul ("does the document state a deadline at all?") when presence is
  independently useful.

Code can act on absence. It cannot act on a confident wrong pick.

## Two things to stop doing

- **Asking the model something code can compute exactly.** If a parser or a regex can
  find it, the model adds nothing and may subtract accuracy.
- **Hiding several judgments inside one question.** You lose the ability to see which
  judgment failed, to tune one without the others, and to test them separately.
