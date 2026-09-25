#!/usr/bin/env python3
"""Vendor-neutral probe for a System One (Jev) endpoint.

Sends each scenario's `state` with one fixed `questions` bundle to JEV_ENDPOINT and prints
the answers, latency and usage. Dependency-free (stdlib only). For looking, not for CI.

Environment:
  JEV_ENDPOINT   full URL that accepts the canonical body {model, state, questions}
                 e.g. https://api.typesafe.ai/v1/systemone  or a gateway's decisions URL
  JEV_API_KEY    bearer token for that endpoint
  JEV_MODEL      model id as that vendor spells it (default: jev-latest)
  JEV_WRAPPER    optional. If your vendor wraps the body, name the wrapper key, e.g.
                 "decisionsRequest"; the canonical body is nested under it.
  JEV_ANSWERS    optional dotted path to the answers map in the response if it is not
                 top-level "answers", e.g. "result.answers".

Usage:
  python probe.py scenarios.json [--repeat N]

Scenario file shape:
  {"questions": {...canonical bundle...},
   "scenarios": {"name": {"state": <any JSON>, "expect": {"q_key": "choice" | "<0.2" | ">0.8"}}}}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value else default


def _dig(obj: dict, dotted: str):
    for part in dotted.split("."):
        obj = obj[part]
    return obj


def call(endpoint: str, key: str, body: dict, wrapper: str | None) -> tuple[dict, float]:
    payload = {wrapper: body} if wrapper else body          # <- adapt here if your vendor wraps differently
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.load(resp)
    return out, time.monotonic() - t0


def check(expect: str, answer: dict) -> bool | None:
    kind = answer.get("type")
    if kind == "choice":
        return answer.get("choice") == expect
    value = answer.get("noul") if kind == "noul" else answer.get("score")
    if value is None:
        return None
    if expect.startswith("<"):
        return value < float(expect[1:])
    if expect.startswith(">"):
        return value > float(expect[1:])
    return None


def render(key: str, a: dict, expect: str | None) -> str:
    mark = ""
    if expect is not None:
        ok = check(expect, a)
        mark = "  ✓" if ok else ("  ✗" if ok is False else "  ?")
    if a.get("type") == "noul":
        return f"    {key:<28} noul={a['noul']:.2f}{mark}"
    if a.get("type") == "choice":
        probs = ", ".join(f"{k}={v:.2f}" for k, v in sorted(a["probabilities"].items(), key=lambda kv: -kv[1]))
        return f"    {key:<28} choice={a['choice']} conf={a.get('confidence', 0):.2f}  [{probs}]{mark}"
    if a.get("type") == "score":
        probs = ", ".join(f"L{k}={v:.2f}" for k, v in a["probabilities"].items())
        return f"    {key:<28} score={a['score']:.2f} conf={a.get('confidence', 0):.2f}  [{probs}]{mark}"
    return f"    {key:<28} {json.dumps(a)[:80]}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios", help="path to scenarios JSON")
    ap.add_argument("--repeat", type=int, default=1, help="send each scenario N times (variance check)")
    args = ap.parse_args()

    endpoint, key = _env("JEV_ENDPOINT"), _env("JEV_API_KEY")
    if not endpoint or not key:
        sys.exit("set JEV_ENDPOINT and JEV_API_KEY (see --help)")
    model = _env("JEV_MODEL", "jev-latest")
    wrapper = _env("JEV_WRAPPER")
    answers_path = _env("JEV_ANSWERS", "answers")

    with open(args.scenarios) as f:
        spec = json.load(f)
    questions = spec["questions"]

    total_in = 0
    for name, sc in spec["scenarios"].items():
        expect = sc.get("expect", {})
        for i in range(args.repeat):
            body = {"model": model, "state": sc["state"], "questions": questions}
            try:
                out, dt = call(endpoint, key, body, wrapper)
            except urllib.error.HTTPError as e:
                print(f"\n== {name}: HTTP {e.code}\n{e.read().decode()[:600]}")
                break
            answers = _dig(out, answers_path)
            usage = out.get("usage", {}) or {}
            tok = usage.get("input_tokens", usage.get("inputTokens"))
            total_in += tok or 0
            cost = usage.get("cost")
            head = f"\n== {name}" + (f" (run {i + 1})" if args.repeat > 1 else "")
            print(f"{head}   model={out.get('model')}  {dt * 1000:.0f} ms  in_tok={tok}" + (f"  cost=${cost:.6f}" if cost else ""))
            for q in questions:
                if q in answers:
                    print(render(q, answers[q], expect.get(q)))
    print(f"\ntotal input tokens: {total_in}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
