# Pedagogy: how this skill teaches, and why

A skill is a lesson plan for a model. This note records the instincts behind `apply-jev`
so that future edits keep its shape. It is written for maintainers, not for the model.

## The learner is capable, literal, and prior-laden

The reader of `SKILL.md` is a strong language model. It does not need to be told what a
probability is. It *does* arrive with a prior that any model is a smaller version of
itself: something you prompt, that writes back. Jev violates that prior in every
direction, and the prior reasserts itself under pressure (the model will drift toward
"ask Jev to summarise" or "let Jev decide the plan"). So the skill's first job is not to
add facts but to **replace a mental model**, and to keep replacing it at each step where
the old one would leak back in.

That is why `SKILL.md` opens with the one sentence ("Jev does not write") and one rule
("code owns control flow…"), and why the rule is restated in applied form in every later
section. Repetition of a principle in new contexts is not padding; it is how a prior gets
overwritten.

## Teach by contrast, then by procedure, then by example

Three moves, in order:

1. **Contrast** establishes the category. System One vs System Two; Jev vs an LLM with
   JSON mode; what Jev is not. A learner who can say what something *isn't* has a boundary
   to reason with.
2. **Procedure** makes judgment reproducible. The six-question fit test, the
   failure-mode→rule table, the three bands. A procedure is something the model can run on
   a case it has never seen, which is the whole point of a skill.
3. **Example** calibrates the procedure. Twelve candidates walked through the test, three
   small worked designs, a worked policy. Examples span domains deliberately so the model
   learns the *shape* of a fit rather than memorising a use case.

## Rules carry their reasons

Every rule in `question-design.md` is stated next to the documented failure mode that
motivates it. This is not decoration. A model that knows *why* a rule exists can judge
when it applies, relax it when it does not, and notice a new situation the rule did not
anticipate. A model given bare imperatives will either over-apply them or ignore them.
"Ask one thing per question because broad questions hide judgments you cannot inspect or
tune" is a rule the model can extend; "ALWAYS decompose" is not.

For the same reason the skill avoids capitalised MUSTs. Emphasis is a weak substitute for
explanation, and it trains compliance rather than understanding.

## Saying no is part of the skill

A skill about a tool has a bias toward using the tool. `apply-jev` counters that
explicitly: the fit test has a *not a fit* verdict, the worked examples include clear
rejections, and the description promises an honest answer to "should I use Jev for this?"
even when it is no. A skill that cannot say no is a sales page, and the model will learn
to distrust it.

## Separate the durable from the perishable

Model versions, prices, limits, endpoint paths and vendor lists change monthly. The
mental model, the fit test and the design rules change rarely. The skill keeps the
perishable facts in a dated section ("Facts that go stale") and in one reference file
(`access.md`), tells the model to re-verify them, and keeps the durable material free of
version numbers wherever possible. Progressive disclosure does the rest: `SKILL.md` is the
procedure; references are loaded when a step needs depth.

## Vendor-neutral by construction

The contract (`{model, state, questions}` → `{model, answers, usage}`) is the thing to
learn. Endpoints, wrappers and auth are per-vendor detail. Teaching the contract first
means the model can adapt to a gateway it has never seen by reading one page, rather than
having to unlearn a hard-coded path. It also keeps the skill honest about what is the
model's behaviour and what is a vendor's wrapper.

## Output formats are scaffolds, not cages

The skill specifies what a fit assessment, a design, and an explanation should contain and
in what order. The purpose is to make the model's *thinking* visible and checkable: a fit
table forces a verdict per candidate with reasons; a design ordered as inventory → state
→ questions → thresholds → evaluation → code forces the decisions to be made before the
code is written. The formats are loose enough to fit any domain.

## Encourage verification over assertion

Where the skill can, it points to an experiment instead of a claim: label examples, sweep
thresholds, inject an instruction and watch which questions move, repeat an input and
measure drift. The probe script exists so the model can propose a concrete check rather
than a confident opinion. Calibration in particular is presented as a population property
to be measured on the user's data, not a promise to be repeated.

## What we deliberately left out

- Long API references. TypeSafe's docs and skill do that better and stay current.
- Domain-specific recipes. They date fast and teach memorisation; the patterns file
  teaches shapes instead.
- Code generators. The skill wants the model to *design* before it writes; a scaffolder
  would invite the reverse.

## How to change it

Add a rule only with its reason. Add an example only if it teaches a shape the existing
ones do not. Move any new fact with a shelf life into the dated section or `access.md`.
When the model's documented failure modes change, update `question-design.md` first,
because everything else derives from it. Run the prompts in `evals/evals.json` before and
after, and add a prompt for any weakness you found.
