# apply-jev

An agent skill that teaches a language model how to **think about** Jev, TypeSafe's
System One decision model: what it is, whether it fits a given problem, and how to use it
correctly. It works in Claude Code, Claude.ai projects, and any agent environment that
loads `SKILL.md`-style skills.

Jev answers typed questions about a `state` with calibrated probabilities. It does not
generate text. That makes it excellent for routing, triage, moderation, guardrails,
relevance scoring, verification and human-in-the-loop gating, and useless for anything
that needs a sentence written or a plan held. Most mistakes come from treating it as a
small LLM. This skill exists to prevent those mistakes and to make the good uses obvious.

## What it teaches

- **The mental model**: System One vs System Two, calibrated probabilities (RLCD), the
  three primitives (Noul, Choice, Score), and what Jev is not.
- **A fit test**: six literal questions that sort any candidate into *strong fit*, *fit
  with code around it*, or *not a fit*, with a dozen worked examples including grey zones.
- **The craft of question design**: decomposition, literal instructions, criteria with
  boundary cases, escape hatches, state filtering, each rule tied to a documented failure
  mode of the model.
- **Deciding with probabilities**: probability vs confidence, three bands, thresholds that
  scale with risk, why bars do not transfer across phrasings or versions.
- **The fact/action split**: code establishes facts, Jev scores actions, a person takes the
  uncertain middle.
- **Evaluation before trust**: labelled sets, adversarial checks, repeatability, pinning.
- **Vendor-neutral access**: the canonical request and response contract, limits and
  errors, and the routes known to serve it, with the caveat that the list drifts.

## Layout

```
apply-jev/
├── SKILL.md                       the skill: procedure, rules, output formats (read first)
├── references/
│   ├── mental-model.md            what Jev is, System One vs Two, RLCD, what it is not
│   ├── fit-test.md                twelve candidates walked through the six-question test
│   ├── question-design.md         failure mode → rule; instructions, criteria, state
│   ├── thresholds.md              probabilities vs confidence; bands; a worked policy
│   ├── patterns.md                fan-out, confidence routing, composite scoring, verify-and-cascade,
│   │                              guardrails, extraction-as-selection, transition scoring, evals
│   ├── access.md                  canonical contract, limits, errors, known access routes
│   └── evaluation.md              the protocol; adversarial checks; the probe script
├── scripts/
│   ├── probe.py                   dependency-free harness for any endpoint speaking the contract
│   └── example-scenarios.json     a support-triage bundle with a happy path, a claim without
│                                  evidence, and an injected instruction
├── evals/evals.json               test prompts used to check the skill itself
├── PEDAGOGY.md                    why the skill is written the way it is
└── LICENSE                        MIT
```

## Install

**Claude Code** (project-local):

```bash
mkdir -p .claude/skills && git clone https://github.com/frty2-ai/apply-jev .claude/skills/apply-jev
```

or user-wide into `~/.claude/skills/apply-jev`. Invoke with `/apply-jev` or just ask a
question that involves Jev, decision models, routing, guardrails, or "should I use Jev
for this?".

**Claude.ai**: add the repository's files to a Project, or paste `SKILL.md` and the
`references/` you need into project knowledge.

**Other agents**: copy the directory into wherever your agent loads skills; the format is
plain Markdown with YAML frontmatter.

## Try the probe

```bash
export JEV_ENDPOINT="https://api.typesafe.ai/v1/systemone"   # or your gateway's URL for the same contract
export JEV_API_KEY="..."
export JEV_MODEL="jev-1.13.0"                                # or the vendor's id for it
python scripts/probe.py scripts/example-scenarios.json --repeat 2
```

It prints each question's answer, latency and token usage, with ✓/✗ against the informal
expectations in the scenarios file. See `references/evaluation.md` for how to use it in an
evaluation protocol.

## Relationship to TypeSafe's official skill

TypeSafe publishes [its own agent skill](https://github.com/typesafe-ai/skills), which is
oriented toward building with its API and reading its live documentation. Use both. Theirs
is the authoritative source for the current API, SDKs and cookbooks; this one is about
judgment: recognising a System One decision, deciding fit honestly, decomposing well,
thresholding sensibly, and evaluating before trusting, whichever vendor serves the model.

## Facts and dates

Model behaviour, limits and prices change. Facts in this skill were checked on
2026-09-25 against `jev-1.13.0`. The skill tells the model to re-verify anything
version-dependent against the vendor's current pages before quoting it.

## Contributing

Issues and pull requests welcome. Good contributions: new worked fit-test candidates
(especially ones that resisted classification), corrections when the model or its docs
change, additional patterns with a clear "what code owns" line, and eval prompts that
expose a weakness in the skill. Keep it vendor-neutral and keep every rule tied to a
reason.

## License

MIT. See `LICENSE`.
