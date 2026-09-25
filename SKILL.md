---
name: apply-jev
license: MIT
description: >
  Teaches how to think about, evaluate the fit of, and correctly use Jev, TypeSafe's
  System One decision model, and System One models in general: models that answer typed
  questions about a state with calibrated probabilities instead of generating text. Use
  this skill whenever the user mentions Jev, TypeSafe, System One, a "decision model",
  noul/choice/score questions, or calibrated probabilities; whenever they are designing
  or reviewing classification, routing, triage, moderation, guardrails, LLM-as-judge,
  evals, relevance scoring or reranking, structured extraction, agent tool-call gating,
  human-in-the-loop thresholds, or any place where code branches on the meaning of text;
  and whenever an existing prompt asks an LLM to "return JSON", a regex is doing semantic
  work, or a chain of if-statements is guessing at intent. Also use it to brainstorm where
  typed decisions could replace fragile parsing or an over-powered LLM call in an app, and
  to answer "should I use Jev for this?" even when the answer is no. Vendor-neutral: works
  whichever API or gateway serves the model. Not for generating text, writing code with a
  model, or swapping the LLM behind a chat or coding agent; Jev does none of those.
metadata:
  version: 0.1.0
  facts-checked: 2026-09-25
  model-version-referenced: jev-1.13.0
---

# Apply Jev

Jev does not write. It reads a `state` you give it, answers the typed questions you wrote
about that state, and returns probabilities your code can branch on. That single fact
changes how you design with it. Most mistakes people make with Jev come from treating it
as a small LLM. It is a different kind of tool: a **probabilistic decision function**
with three output types, trained (via what TypeSafe calls RLCD, reinforcement learning
for calibrated decisions) so that a returned 0.8 means "right about 80% of the time
across many such answers", not "sounds confident".

Hold this rule while you work: **code owns control flow, facts and side effects; Jev
supplies narrow, typed judgments at the edges; a person or a reasoning model takes the
cases Jev is unsure about.** Everything below is that rule applied.

## Recognise which job you are doing

Users arrive in one of four modes. Name the mode to yourself before answering, because
each wants a different shape of response.

| Mode | What the user said, roughly | What to produce |
| --- | --- | --- |
| **Explain** | "What is Jev / System One?" "How is it different from GPT with JSON mode?" | The mental model in their terms, then one concrete example from their domain. Read `references/mental-model.md`. |
| **Assess fit** | "Should I use Jev for X?" "Would this work with a decision model?" | A verdict with reasons, using the fit test below. Say no when it is no. |
| **Design and build** | "Use Jev to route/score/verify/gate…" | A decomposed question bundle, threshold policy, evaluation plan, then code. |
| **Review or brainstorm** | "Look at my app/code and tell me where Jev fits" | An applicability table: candidate decisions, verdict per candidate, what stays in code. |

If the user wants to *replace the model behind a chat or coding agent* with Jev, stop and
explain that it cannot do that job (no generation, no tool-use loop) and redirect to where
Jev fits *inside* such a system: gating tool calls, judging outputs, routing, guardrails.

## The fit test

Run every candidate through these six questions. Be literal; the value of the test is in
its discipline.

1. **Is the answer one of N, a yes/no, or a position on a rubric you can write down?**
   If you cannot enumerate the answer space, Jev cannot return it. "Summarise this"
   fails; "which of these five topics is this about" passes.
2. **Is the input text (or JSON of text)?** Jev is text-only. Images, audio and video
   must be turned into typed fields by something else first (an OCR pass, a vision model
   with structured output, a transcript). Jev then judges the fields.
3. **Could code compute it exactly?** Arithmetic, counting, date ordering, string
   equality, schema validation, lookups. If yes, do it in code. Jev is not a calculator
   and its own docs say so. Reserve it for what needs *reading*.
4. **Is it one hop?** "Does this message ask for a refund?" is one hop. "Would a
   reasonable adjuster, given the policy's exclusions and the claimant's history, likely
   approve this?" is several. Multi-hop, double-negative, or "a property of a property"
   questions lose accuracy. Split them or hand them to a reasoning model.
5. **Can the state be small and relevant?** Accuracy falls as unrelated detail grows
   (TypeSafe calls this context rot). If the decision needs a 40-page document, retrieve
   or filter first, then ask about the relevant part. Hard limits as of `jev-1.13`: 32k
   tokens for state plus the longest question, 64k for the whole request.
6. **Does the caller benefit from a calibrated probability rather than a label?**
   If every answer will be acted on blindly, an ordinary classifier may do. Jev earns its
   place when "I am not sure" must route somewhere: a human queue, a bigger model, a
   confirmation step.

Score the candidate:

- **Strong fit**: passes all six. Typical: routing, triage, moderation, relevance,
  rubric grading, verification of a claim against evidence, gating an agent's tool call.
- **Fit with code around it**: fails 2, 3 or 5 in a fixable way. Pre-process the media,
  move the arithmetic into code, filter the state, then it becomes a strong fit. Most
  real cases land here.
- **Not a fit**: fails 1 or 4 irreducibly, or needs an explanation, or needs the model
  to generate anything. Say so plainly and suggest what does fit: a generative model,
  a reasoning model, plain code, or a human.

`references/fit-test.md` walks a dozen candidates through this procedure, including the
grey-zone ones.

## Find the decision, not the task

People describe tasks ("triage tickets", "check compliance", "moderate posts"). Jev
answers decisions. Work backward from the action the software will take, and ask what
judgments that action actually depends on. A ticket router does not need "understand
the ticket"; it needs *which team*, *how urgent*, *is a refund requested*, *is the
customer angry*. Four questions, one call, code decides.

Separate two things that are easy to blur:

- **Facts** are what the evidence shows. Where a fact can be established by code or by a
  dedicated verifier (a schema check, a database lookup, a vision model's typed output),
  establish it there and put the result in the state. Do not ask Jev to *be* the
  evidence.
- **Actions** are what to do next given the facts and the text. This is Jev's natural
  role: `advance | retry | defer | escalate`, `approve | confirm | reject`, `pass |
  review | block`.

The split matters because state is data to Jev, not a hostile input. Text written to
steer the answer ("the check already passed, move on") can move a judgment question.
It is much less able to move a question phrased over typed fields ("is
`verifier.result.present` true?"). Keep the fact questions literal and field-bound, let
the action questions carry the judgment, and let code refuse to act on an action whose
facts do not support it.

## Choose the primitive by what the answer means

| You need | Primitive | Returns | Watch for |
| --- | --- | --- | --- |
| Whether a condition holds | **Noul** | `noul` in 0..1, the probability of yes | No separate confidence; 0.5 means "as likely yes as no", not "moderately". Word it so yes means the thing you are checking *for*. |
| One option from a set | **Choice** | `choice`, `probabilities` over all options, `confidence` | Relative: it settles *which*, and can pick a winner even when every option is a poor fit. Add a `none` / `other` option whenever nothing may match. Up to 255 options. |
| A position on an ordered rubric | **Score** | `score` (can land between levels), `legend`, `probabilities`, `confidence` | Levels must describe concrete situations, not "1 to 10". Use the expectation to threshold, never to reconstruct an exact number. 2 to 10 levels. |

A Choice over options and one Noul per option answer different questions. The Choice says
which is best; the Nouls say whether each holds at all. Use both when you need both
(pick a category *and* decide whether to assign one).

## Write the question bundle

This is the craft, and TypeSafe's own guide calls decomposition "probably the most
important concept". Every rule below exists because of a documented way `jev-1.13` goes
wrong; `references/question-design.md` maps each to its failure mode.

- **One judgment per question.** "Is this spam?" hides six judgments. Ask them:
  requests credentials, unexpected reward, time pressure, sender/domain mismatch, link
  mismatch, disguised destination. Combine in code. You gain inspectability, tunable
  weights, and questions you can test one at a time.
- **Ask exactly what you mean.** Jev answers the question you wrote, not the one you
  meant. Scoping words, negations and implied conditions are read at face value. When a
  wrong answer makes you say "well, what I really meant was…", that sentence is the
  missing half of the instruction.
- **Point at the state by name.** Use backticked paths: `` `ticket.messages[0].text` ``,
  `` `verifier.printed_page_visible` ``. It removes ambiguity and shortens the hop.
- **Put boundaries in the criteria.** For a Noul, describe what a yes and a no look like,
  with the borderline cases on the side you want them. For a Choice, say what each option
  *covers*, what it is *not for*, and give two examples. For a Score, each level is a
  scene, not a number. Criteria and instructions must agree; a Noul whose `true` describes
  a no performs badly.
- **Filter the state first.** Send the fields the questions need. Structured JSON with
  descriptive keys beats a blob. Related things the decision must compare (message +
  policy + record) belong together in one state.
- **Use structure when it clarifies.** `instructions` and `criteria` accept objects and
  arrays. Put the question in one field and the data it refers to in others. A schema, a
  taxonomy, or a database row is already JSON; pass it as such.
- **Always give an escape hatch.** A `none`, `not_stated`, `other`, or `out_of_range`
  option turns "the model guessed" into "the model reported absence". Code can act on
  absence; it cannot act on a confident wrong pick.
- **Ask many questions at once.** Questions over one state run in parallel and are
  answered independently; adding questions barely changes latency and adds only their
  tokens. Include speculative branch questions up front and let code read the relevant
  ones. A second call is only needed when an answer changes what state you fetch or what
  options exist.
- **Do not expect cross-question consistency.** `P(refund)` and `1 − P(not refund)` need
  not agree, and a yes/no Choice does not produce the same number as a Noul. Ask each
  decision once, one way, and enforce any identities in code.
- **Extraction is selection.** Jev cannot write the value out. Find candidates in code
  (regex, parser, a generative model) and ask Jev to pick the right one, with a `none`
  option. Dates: ask for month, day, year, weekday as Choices and assemble in code.

## Decide with thresholds, not argmax

Read the whole distribution, not just the top label. For Choice and Score, `confidence`
summarises how peaked `probabilities` is (all mass on one option → 1.0; spread evenly →
low). For Noul, the probability *is* the signal. Then:

- **Three bands.** High: act automatically. Middle: proceed with caution (confirm with
  the user, flag for review, gather more). Low: do not act; route to a person or a
  reasoning model. An explicit `uncertain` outcome is application logic over the number
  you already have; it costs no second call.
- **Thresholds scale with risk.** One floor for "genuinely unsure" (often ~0.5–0.6), then
  per-action bars: read-only actions can act at moderate confidence; destructive,
  irreversible or costly actions need much more, or a confirmation step. Your code encodes
  the risk tolerance; the model does not know the stakes.
- **Argmax is fine when only ranking matters.** If you just need the best option and any
  option is acceptable, take the top one and skip the threshold theatre.
- **Never carry a threshold across phrasings or versions.** A bar tuned on a Noul does
  not transfer to a Choice. A bar tuned on `jev-1.13.0` may not survive `jev-latest`
  moving. Pin the versioned model id once thresholds are tuned; the response's `model`
  field reports what actually answered, so log it.
- **Calibration is a population property.** A 0.8 is right about 80% of the time *across
  many answers*. It is not a promise about this one. That is why the middle band exists.

`references/thresholds.md` has the arithmetic and a worked policy.

## Evaluate before you trust

A typed answer is not a correct answer. Before wiring Jev into anything that acts:

1. **Label 50–200 real examples** of the decision, including the annoying edge cases.
2. **Run the bundle, sweep the thresholds**, and plot accuracy against confidence. Pick
   bars from the curve and the cost of each kind of error, not from a cookbook.
3. **Attack it.** Put a steering instruction in the state ("mark this as approved"), a
   confident claim with no evidence, evidence for the wrong item, contradictory fields.
   Watch which questions move. Field-bound fact questions should not; if a judgment
   question does, that is the question code must not trust alone.
4. **Repeat identical inputs** a few times. Jev is designed to be stable; drift beyond a
   couple of hundredths means your state carries something incidental.
5. **Record the versioned model id** with every stored decision.

`scripts/probe.py` runs a scenarios file through any endpoint that speaks the canonical
request shape and prints answers, latency and usage. `references/evaluation.md` gives
the protocol and what "good" looks like.

## Implement without marrying a vendor

Every route to Jev carries the same core contract, sometimes wrapped:

```json
{ "model": "jev-1.13.0",
  "state":  <string | object | array>,
  "questions": {
    "<your_key>": { "type": "noul"|"choice"|"score",
                    "instructions": <string|object|array>,
                    "criteria": <noul: {true,false} | choice: {option: description|null} | score: [level, ...]> } } }
```

and returns `{ "model": "<versioned id that answered>", "answers": { "<your_key>": {...} }, "usage": {...} }`.
Question keys are for your code and are not shown to the model, so the meaning must live
in `instructions` and `criteria`.

TypeSafe serves this natively; several API gateways and SDK frameworks expose it under
their own paths, auth and sometimes a wrapper object. Do not hard-code assumptions from
one vendor into another. Read `references/access.md` for the shape, limits and error
codes, and the current list of known routes with the caveat that it drifts. Keep API
keys server-side. Retry 429/529 with backoff.

Put the questions and thresholds in one reviewable place (one module, one config file).
They are the part a human must read, and the part that changes when the model does.

## Output formats

**Fit assessment** (Assess or Review mode): use this table, one row per candidate decision.

```
| Candidate decision | Verdict (strong / with code around it / not a fit) | Why (which fit-test items) | Primitive(s) | What stays in code |
```

Follow with the two or three highest-value candidates expanded into draft questions.

**Design** (Design mode): deliver in this order. Decision inventory (facts vs actions) →
state shape (fields, sources, what is filtered out) → question bundle (keys, primitive,
instructions, criteria) → threshold policy (bands per action, floors, pinned model) →
evaluation plan (labels, attacks, sweep) → code. Constants together in one file.

**Explain** (Explain mode): lead with the contrast that matters to *this* user (vs an LLM
with JSON mode, vs a classifier, vs a rules engine), then one example in their domain,
then the two or three limits most likely to bite them.

## Three small examples

**Agent tool-call gate.** State: `{task, proposed_call, context}`. Questions:
`reversible` (Noul: only reads or changes things inside the project and can be undone),
`serves_task` (Noul: a reasonable next step toward `task`). Policy: auto-run only if both
≥ 0.9; otherwise ask the human. Code, not Jev, decides what "destructive" means for this
repo, and the deterministic denylist runs first.

**Verify an LLM draft before it ships.** State: `{policy_excerpts, customer_question,
draft_reply}`. One Choice: `supported | unsupported | declined`, each with a criterion
about whether every fact in the draft appears in the excerpts. Route `unsupported` and
low-confidence `supported` to a person. Cheaper than a second LLM, and it cannot be talked
into agreeing by the draft's own prose as easily as an LLM judge can.

**Scripted multi-step flow.** Code holds the checklist and knows the current step. Per
turn, state = `{current_step, last_user_turn, typed_result_from_verifier}`; questions =
`step_satisfied` (Noul, bound to verifier fields), `next_action` (Choice: advance,
continue, retry_with_hint, defer, escalate), plus a Noul for each interrupt condition.
Code advances only if the field-bound fact passes *and* `advance` clears its bar. Jev is
the transition scorer; the state machine stays in code where it can be audited.

## Facts that go stale

Verified 2026-09-25 against TypeSafe's docs. Re-check before quoting: current model is
`jev-1.13.0` (aliases `jev-latest`, `jev-preview`); TypeSafe list price $0.042 per million
input tokens, output free; gateways price separately; ~100 ms typical direct latency,
several hundred ms through a gateway; rate limits described as dynamic. The jaggedness page
(`docs.typesafe.ai/model-jaggedness/<version>`) is versioned; read the one for the model
you are using.

## Where to go next

| Need | Read |
| --- | --- |
| The mental model, System One vs System Two, RLCD, what Jev is not | `references/mental-model.md` |
| A dozen candidates walked through the fit test, including grey zones | `references/fit-test.md` |
| Writing instructions and criteria; each rule tied to a failure mode | `references/question-design.md` |
| Probabilities vs confidence; bands; risk-scaled bars; worked policy | `references/thresholds.md` |
| Fan-out, confidence routing, composite scoring, intent routing, verify-and-cascade, guardrails, extraction-as-selection, transition scoring | `references/patterns.md` |
| Canonical request and response, limits, errors, known access routes | `references/access.md` |
| Evaluation protocol, adversarial checks, repeatability, the probe script | `references/evaluation.md` |
