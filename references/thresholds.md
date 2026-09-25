# Probabilities, confidence and thresholds

## What comes back

| Primitive | Fields | Read it as |
| --- | --- | --- |
| Noul | `noul` | P(yes). Near 1 strong yes, near 0 strong no, near 0.5 genuinely uncertain. No separate confidence. |
| Choice | `choice`, `probabilities`, `confidence` | `choice` is the top option. `probabilities` is the full distribution (sums to 1). `confidence` collapses its shape into 0..1. |
| Score | `score`, `legend`, `probabilities`, `confidence` | `score` is the probability-weighted position along your levels and can fall between them. `legend` maps level index to your description. |

`confidence` is a statistic *computed from* `probabilities`: all mass on one option → 1.0;
spread evenly → low. TypeSafe provides it as a convenient default and gives you the full
distribution so you can compute something else (a margin between top two, entropy, mass
on an "acceptable" subset) when your problem wants it.

## Probability vs confidence: which to threshold

- **A single yes/no decision**: threshold the Noul directly.
- **Pick one, act on it**: threshold `confidence` (is there a clear winner?) and then
  branch on `choice`.
- **Pick one, but some options are acceptable substitutes**: threshold the *summed*
  probability of the acceptable set, not `confidence`. Low confidence between two fine
  options is not a problem.
- **Just rank**: take argmax or sort by probability. No threshold needed.
- **Score**: threshold `score` against a level boundary (e.g. ≥ 1.5 on a 0–2 rubric), and
  separately check `confidence` if a flat distribution should send the case to review.

Do not reconstruct exact quantities from a Score expectation. 1.43 on a 0–2 severity
rubric means "probably level 1, maybe 2", not "43% of the way to blocking".

## The three bands

```
        0 ──────────── low ──────┼──── middle ─────┼─────── high ───────── 1
                   do not act    │ act with caution │  act automatically
              route to a person  │ confirm / flag / │
              or a bigger model  │ gather more      │
```

The middle band is not a failure to decide. It is the model saying "I don't know", which
is the signal that makes the system trustworthy. Make the `uncertain` outcome explicit in
your code and measure how often it fires; that number is your review workload.

## Thresholds scale with risk

A threshold is not one number. Gate each action by the cost of being wrong about it:

```python
action = answers["intent"]

if action.confidence < 0.6:            # genuinely unsure: nobody acts
    route_to_human(request)
elif action.choice == "check_balance": # read-only, recoverable: 0.6 is plenty
    show_balance(account)
elif action.choice == "approve_transfer":
    if action.confidence > 0.85:       # high stakes, high confidence: proceed with confirmation
        confirm_then_execute(account)
    else:                              # high stakes, moderate confidence: verify intent first
        ask_user_to_confirm(account)
```

The floor catches "unsure about anything". Above it, destructive or irreversible actions
need a higher bar than read-only ones, or a confirmation step. Your code knows the stakes;
the model does not.

## A worked policy (guardrail battery)

Four hazard Nouls plus a severity Score, one request per message. Two thresholds per
hazard and a severity override, under a named policy:

```python
HAZARD_ACTION = {"jailbreak": "block", "harmful_request": "block",
                 "medical_advice": "review", "self_harm": "support"}
PRECEDENCE = ["support", "block", "review", "pass"]
POLICIES = {
  "strict":     {"review_at": 0.35, "act_at": 0.70, "severity_block": 2.0},
  "permissive": {"review_at": 0.35, "act_at": 0.85, "severity_block": 2.0},
}

def route(nouls, severity, policy):
    fired = []
    for hazard, p in nouls.items():
        if p >= policy["act_at"]:      fired.append(HAZARD_ACTION[hazard])
        elif p >= policy["review_at"]: fired.append("review")
    if severity >= policy["severity_block"]:
        fired = ["block" if a == "review" else a for a in fired]
    return next((a for a in PRECEDENCE if a in fired), "pass")
```

The same probabilities produce different actions under different policies. That is the
design: the model assesses, the product decides how much evidence it wants before acting.

## Where thresholds come from

Not from a cookbook. From your data:

1. Label real examples (50–200 to start).
2. Run the bundle. For each question, plot accuracy (or precision/recall) against the
   probability or confidence.
3. Choose bars from the curve *and* the cost of each error type. A false auto-approve may
   cost far more than a false review.
4. Measure the review rate the bars imply. If a person must look at 40% of traffic, the
   bars or the questions need work.

## Do not carry thresholds across

- **Phrasings.** A bar tuned on a Noul does not transfer to a yes/no Choice; TypeSafe's own
  example shows the two producing different numbers for the same question.
- **Questions.** Each question gets its own bar.
- **Model versions.** Aliases (`jev-latest`, `jev-preview`) move when TypeSafe ships.
  Once thresholds are tuned, pin the versioned id (`jev-1.13.0`) and migrate on your own
  schedule. Log the `model` field from every response; it reports what actually answered.

## Combining answers in code

Weighted sums suit compensating preferences (a candidate strong on two dimensions and weak
on one). Precedence rules suit "any serious violation blocks". Do not blur them: "sum of
hazards ≥ 1.2" is a different policy from "any hazard ≥ 0.7", and only one of them is what
you mean.

When you have labelled outcomes, the probabilities make good features for a small
classical model (logistic regression, gradient boosting) that learns the combination for
you. Keep the raw answers stored so weights can change without re-running inference.
