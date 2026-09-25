# The fit test, worked

The six questions from `SKILL.md`, applied to a dozen candidates. Read this when a
candidate is in the grey zone, or to calibrate your own verdicts before giving one.

The six, for reference:

1. Enumerable answer space?
2. Text input (or typed fields derived from non-text)?
3. Could code compute it exactly?
4. One hop?
5. Small, relevant state?
6. Does the caller need a calibrated probability, not just a label?

Verdicts: **strong fit**, **fit with code around it**, **not a fit**.

---

### Route support tickets to a team

1 yes (billing / orders / account / other). 2 yes. 3 no. 4 yes. 5 yes (ticket + a few
account fields). 6 yes (send unsure ones to a human).
**Strong fit.** Choice for team, Nouls for refund-requested and frustration, one call.

### Decide whether an agent's proposed shell command is safe to auto-run

1 yes (safe / unsafe, or a Choice over allow / confirm / deny). 2 yes (the command and
the task as text). 3 partly: a denylist and a "touches paths outside the repo" check are
exact and belong in code. 4 yes if phrased as "only reads or changes files inside the
project and can be undone". 5 yes. 6 yes (the whole point is a bar for auto-approval).
**Fit with code around it.** Deterministic checks first, then two Nouls (`reversible`,
`serves_task`) with a high bar. Jev never overrides a denylist.

### Summarise a meeting transcript

1 no. Nothing to enumerate.
**Not a fit.** Use a generative model. Jev could *judge* the summary afterwards
("does `summary` mention the decision recorded in `transcript`?"), which is a different,
fitting task.

### Is this generated answer supported by the retrieved passages?

1 yes (supported / unsupported / declined). 2 yes. 3 no. 4 yes when the criteria are
specific ("every fact, number and timeframe in `answer` appears in `passages`"). 5 yes if
you pass only the passages actually retrieved. 6 yes.
**Strong fit.** This is the verify-then-ship pattern; cheaper than a second LLM and harder
to talk into agreement.

### Extract the invoice total from an email

1 as written, no: the answer is an open number. Reframed, yes: find every currency
amount with a regex, then ask which one is the total.
3 partly: finding candidates is code; choosing among them is judgment.
**Fit with code around it.** Extraction becomes selection with a `none` option. The same
move works for dates (ask month/day/year as Choices, assemble in code), emails, IDs.

### Is this claim covered under the policy?

1 yes. 2 yes. 3 no. 4 **no**: "covered" bundles exclusions, limits, dates, driver
eligibility, documentation and more. 5 borderline (policy + claim is a lot of state).
**Fit with code around it, after decomposition.** Ask the atomic Nouls (exclusion applies,
within limit, within period, documentation sufficient, rental item eligible…), compute the
date and amount comparisons in code, and let code or a person combine. Never ask the
composite question and act on it.

### Sort a million documents into a 400-node taxonomy

1 yes but 400 > 255 options, and a flat pick over hundreds of near-synonyms is weak.
**Fit with code around it.** Walk the tree: one Choice per level whose options are the
children (with their subtrees as descriptions), beam-search when probabilities are close.
Jev's speed and cost are what make a million items feasible at all.

### Grade student essays on a 1–10 scale

1 as "1 to 10", no: bare numbers are not a rubric. As five described levels, yes.
6 yes (flag borderline grades for a teacher).
**Fit with code around it.** Write levels as concrete scenes. Consider splitting into
dimensions (argument, evidence, clarity) as separate Scores and combining with weights you
own, so a teacher can see *why*.

### Decide the next step in a scripted, multi-step process

1 yes if code presents a small menu of allowed transitions (advance / repeat / defer /
escalate). 4 yes when the state is only the current step, the latest input, and typed
results from any verifier. 5 yes for that reason. 6 yes.
**Strong fit as a transition scorer; not a fit as the state machine.** Jev has no memory
and sees one snapshot; code holds the plan, the ordering and the prerequisites, and asks
Jev to score the edge each turn. If you find yourself sending the whole checklist every
time, you have inverted the design.

### Detect prompt injection or jailbreak attempts in user messages

1 yes. 2 yes. 3 no. 4 yes. 5 yes. 6 yes (review band).
**Strong fit, with a caveat.** A battery of Nouls (override attempt, harmful request,
self-harm signal…) plus a severity Score, thresholded to pass / review / block / support.
Jev's own docs note adversarial content can move it, so pair it with deterministic
checks and test on real attack strings. It is a strong first line, not the only line.

### Compare two dates and tell me which is earlier

3 yes, trivially.
**Not a fit.** Code. If the dates are buried in prose, Jev can *read out the parts*; the
comparison stays in code.

### Explain to the customer why their request was declined

1 no, and it requires generation.
**Not a fit.** Use a generative model. Jev can decide *whether* to decline and *which*
reason category applies; the LLM writes the sentence from the category.

### Score the relevance of 30 retrieved passages to a query

1 yes (a Noul per passage, or a Score over described relevance levels). 5 yes if you send
one passage per question in structured instructions, or batch passages as an array with
one question per index. 6 yes (threshold, or take top-k by probability).
**Strong fit.** TypeSafe reports this raising retrieval accuracy on a legal benchmark;
verify on your corpus.

---

## Reading the pattern

Notice what moved candidates from "not a fit" to "fit": reframing generation as
selection, splitting a composite judgment into atomic ones, moving exact work into code,
shrinking the state. Those four moves *are* the skill. When a user's candidate fails the
test, try each move before saying no; when it passes only after the moves, say so, because
the moves are the design.

Notice also what never moved: anything that needs a sentence written, a plan held across
turns, or a chain of reasoning shown. Those go to a generative or reasoning model, and Jev
can sit in front of or behind them as the router or the verifier.
