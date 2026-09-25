# Patterns

Compositions of the three primitives with code. Each entry says what problem it solves,
how the questions are shaped, and what code owns. Names follow TypeSafe's documentation
where one exists; the last three are common shapes that its cookbooks cover under other
titles.

## Speculative fan-out

**Problem.** A workflow needs different follow-up judgments depending on an earlier one
(bug reports need severity; billing tickets need refund-requested).

**Shape.** Ask every branch's questions in one request. They run in parallel over the same
state; extra questions barely change latency. Code reads the branch that applies and
ignores the rest.

**Code owns.** The decision tree. A second request is warranted only when an answer changes
which state to fetch or which options exist.

## Confidence-gated routing

**Problem.** The same classifier serves actions with very different consequences.

**Shape.** One Choice (or Noul). Code applies a floor for "unsure about anything", then a
per-action bar proportional to the stakes; high-stakes actions get a confirmation step in
the middle band.

**Code owns.** The bars, the confirmation UX, the human queue. See `thresholds.md`.

## Composite scoring

**Problem.** Rank items on several criteria at once, and be able to explain the ranking.

**Shape.** One Score per dimension, each with described levels. Normalise to 0..1 in code
and combine with weights you control. Different roles, different weights, same inference.

**Code owns.** Weights, normalisation, the final ranking. Store the raw scores so weights
can change without re-running the model.

## Intent routing

**Problem.** Not every request deserves an expensive handler. Some need a database
lookup, some a specialist LLM with domain context, some a person.

**Shape.** A Choice for intent and a Score for complexity, one call. Code routes:
deterministic handler, specialist model, or human, with the confidence floor sending the
unclear ones to a person.

**Code owns.** The handler table and what "too complex to automate" means.

## Verify, then ship (and the cascade)

**Problem.** An LLM drafted something (a reply, an extraction, a summary). Is it grounded?

**Shape.** State = `{source_material, question, draft}`. One Choice over
`supported | unsupported | declined`, each criterion explicit about "every fact, number,
timeframe and promise in the draft appears in the source". Optionally Nouls for specific
failure kinds.

**Code owns.** What happens on `unsupported` (retry with a bigger model, hand off) and the
confidence bar for shipping `supported`.

**The cascade.** Use a small, cheap generative model for the first draft, Jev to verify,
and escalate to the expensive reasoning model only when verification fails. Most of the
quality at a fraction of the cost; the Jev call is the part that makes the cheap first
pass safe.

## Guardrails on both sides of an LLM

**Problem.** System prompts are exactly where a jailbreak talks its way past; a second LLM
as guard is slow, costly and also talkable.

**Shape.** One request per message: a Noul per hazard (override attempt, harmful request,
medical/legal advice, self-harm signal…) plus a severity Score. Screen inputs on the way
in and outputs on the way out; the two batteries ask the same things from opposite sides
("does the user ask for it" / "did the reply give it").

**Code owns.** Thresholds, actions per hazard (block / review / support path), precedence,
and the deterministic checks that run first. Jev's docs note adversarial text can move it;
test on real attack strings and treat it as a strong first line rather than the only one.

## Extraction as selection

**Problem.** You need a value out of text, and Jev cannot write values.

**Shape.** Code finds candidates (regex for amounts, emails, IDs; a parser for structure;
or a generative model proposing options). Jev picks the intended one via a Choice with a
`none` option. For dates: Choices for month, day, year, weekday, week offset, each with
`none`/`out_of_range`; code assembles the `date` and does all comparison.

**Code owns.** Candidate generation, assembly, normalisation, validation. The model never
does the calendar math.

## Hierarchical classification

**Problem.** A taxonomy with hundreds of leaves; a flat Choice is too wide (255 max) and
too confusable.

**Shape.** One Choice per level; options are the current node's children, each described
by its subtree so the model can see what lives under a branch before committing. Keep
several paths alive (beam search) when probabilities are close.

**Code owns.** The tree walk, the beam, the stopping rule.

## Reranking and relevance for retrieval

**Problem.** BM25 or embeddings return plausible-looking passages that do not answer the
query.

**Shape.** One question per query–candidate pair ("does `passage` answer `query`?") as a
Noul, or a Score over described relevance levels; batch the shortlist into one request.
Add a Noul for "does the document contain an answer at all?" so the pipeline can decline
instead of hallucinating.

**Code owns.** Top-k, thresholds, what reaches the answering model.

## Transition scoring for scripted workflows

**Problem.** A multi-step process (an intake, a checklist, a wizard) must adapt to what the
user just did without letting a model wander off the script.

**Shape.** Code holds the steps, their order and prerequisites, and knows the current
step. Per turn, state = `{current_step, latest_input, typed_verifier_result}` (small, no
whole-checklist dumps). Questions: a field-bound Noul for "is the current step satisfied
by `verifier_result`" (never by what the user said), a Choice over the *allowed*
transitions (`advance | continue | retry_with_hint | defer | escalate`), and a Noul per
interrupt condition (safety, suspected fraud, request for a human).

**Code owns.** The state machine, the menu of transitions, the pass predicate over
verifier fields, the bars per transition, and the rule that `advance` requires both the
fact and the action to clear. Jev scores the edge; it never holds the plan.

## Judging and evals at scale

**Problem.** You need to grade thousands of model outputs or agent traces against a
rubric, repeatably and cheaply.

**Shape.** State = `{task, trace_or_output, rubric_context}`. Nouls for each rubric item
("did the trace call a tool the task did not need?"), a Score for overall quality with
described levels, a Choice for failure mode with a `none` option. One request per item.

**Code owns.** Aggregation, regression thresholds, which items go to a human grader. Jev's
stability under repetition is what makes trend lines meaningful here; verify it on your
own traces.

## Choosing among patterns

Start from the action the software will take and work backward to the judgments it needs;
the pattern falls out. If you are unsure, fan-out plus confidence-gated routing covers most
first builds: ask everything you might need, route on what you get, send the middle band
to a person, and iterate from there with labelled data.
