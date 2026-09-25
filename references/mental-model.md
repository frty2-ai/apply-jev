# The mental model

Read this when a user needs Jev *explained*, or when you catch yourself reasoning about it
as if it were a small language model.

## One sentence

Jev is a model that reads a state and answers typed questions about it with calibrated
probabilities. It never generates text.

## System One and System Two

TypeSafe borrowed the names from Kahneman. System One is fast, intuitive judgment: is
this angry, which team owns this, does this sentence support that claim. System Two is
slow, deliberate reasoning: plan, derive, compute, explain. Language models (especially
reasoning models) are built to do System Two work in public, writing out their thinking.
Jev is built to do System One work in private and hand you a number.

That split tells you where each belongs. A workflow with twenty small judgments and one
hard piece of reasoning wants twenty Jev questions and one reasoning-model call, not
twenty-one LLM calls, and not one giant prompt that hides the twenty judgments inside
prose.

## What the API actually is

Three primitives, one request, all answered in parallel over the same state:

- **Noul**: a yes/no question. Returns `noul`, the probability of yes (0..1). No separate
  confidence; the probability is the signal.
- **Choice**: pick one from options you define (up to 255). Returns `choice`,
  `probabilities` over every option (sum to 1), and `confidence` derived from how peaked
  that distribution is.
- **Score**: place the state on an ordered rubric you define (2 to 10 levels). Returns
  `score` (a probability-weighted position that can land between levels), `legend`,
  `probabilities` over levels, and `confidence`.

`state` is a string, JSON object, or array of text. Question keys are yours; they are not
shown to the model. `instructions` and `criteria` carry all the meaning and may be strings,
objects or arrays.

## Why "calibrated" is the whole point

TypeSafe trains Jev with what it calls RLCD, reinforcement learning for calibrated
decisions, as a third post-training path alongside RLHF (chat) and RLVR (reasoning). The
objective is not "say what people prefer" but "return a probability that matches how often
you are right". Across many answers, the things it marks 0.2 should happen about 20% of the
time and the things it marks 0.8 about 80%.

Two consequences:

1. **The middle of the range is meaningful.** An LLM asked for a probability tends to
   cluster at the confident ends; Jev is designed to spread mass when the case is genuinely
   ambiguous. That spread is the product feature: it is where your human-review queue comes
   from.
2. **Calibration is about populations, not instances.** A 0.8 on one answer is not a
   promise about that answer. Design policies over many decisions (bands, review rates,
   error costs), not proofs about one.

TypeSafe describes it as consistent under repetition (its cookbook reports a per-question
standard deviation around 0.01 over repeated calls). Treat that as a property to verify on
your own inputs, not a guarantee.

## How it differs from an LLM with structured output

Modern LLMs can return schema-constrained JSON, so "typed output" alone is not the
difference. The differences that matter:

| | LLM with JSON mode | Jev |
| --- | --- | --- |
| Training objective | Preferred text (RLHF) or verified reasoning (RLVR) | Calibrated decisions (RLCD) |
| What you get | A value the model chose to write | A distribution over the answer space you defined |
| Uncertainty | Whatever the model says about itself | A probability meant to be acted on |
| Repeatability | Sampling noise, even at temperature 0 | Designed to be stable |
| Speed and cost | Seconds, cents | ~100 ms direct, fractions of a cent per thousand tokens |
| Explanation | Can write one | Cannot |
| Generation | Yes | No |
| Reasoning depth | Multi-hop, with chain of thought | One hop, literal |

Use the LLM when you need generation, explanation, or multi-hop reasoning. Use Jev when you
need many fast, cheap, calibrated judgments that code will branch on. Use both when a
system needs both: Jev to route and verify, the LLM to write.

## What Jev is not

- **Not a chat or coding model.** There is no setting that makes a coding agent run on
  Jev. It cannot stream text, call tools, or edit files.
- **Not a planner.** It has no memory between calls and sees one snapshot. It can score a
  proposed next step; it cannot hold the plan. Keep state machines and control flow in
  code.
- **Not a calculator, counter or calendar.** Do arithmetic, counting and date comparison
  in code. Ask Jev to *read* the parts (which month, which day) and assemble them yourself.
- **Not a security boundary.** State is data, and adversarial text in the state can move a
  judgment. A guard built on Jev sits beside deterministic checks, not instead of them.
- **Not multimodal.** Text only. Pre-process images, audio and video into typed fields.
- **Not fine-tunable.** The same weights serve everyone. You shape behaviour through the
  state, the instructions and the criteria.

## The three architectures

TypeSafe's own framing is useful when a user is deciding what kind of system they are
building:

- **Traditional software**: reliable primitives composed into a decision tree. No semantic
  understanding.
- **LLM agent**: a model reads instructions and chooses its next action in a loop. Powerful,
  but every loop is a chance to go off the rails, and it wants a human watching.
- **AI-powered software**: code owns the control flow; a model appears only where the
  system needs programmable common sense over unstructured input, each use atomic and
  constrained.

Jev is built for the third. When a user's design is really the second, help them notice
which of its judgments could be pulled out into the third.
