# Live Consultant

Live Consultant is an independent Codex plugin by Ali Zeidan for integrated
business diagnosis, bold direct-response offer creation, market and idea
validation, sales, funnels, websites, Meta ads, analytics, operations, and
decision support.

## Core behavior

- Finds the binding constraint while keeping every relevant tactic available for
  explanation, ideation, and bounded testing; the constraint changes emphasis
  and expected consequences, not access.
- Infers the exact buyer, trigger, business model, geography, channel, stage,
  and current decision before researching or asking questions.
- Asks only decision-changing questions, then researches the exact niche with
  claim-matched current sources instead of substituting generic industry advice.
- Uses the Sabri/King Kong mindset without compliance, proof, or implementation
  dilution during offer ideation.
- Provides a first-class `$sell-like-crazy` skill with the complete eight-phase
  buyer-to-sale system, frameworks, cases, original niche examples,
  integrations, and exact source locators.
- Infers the outcome, selects every skill with a distinct contribution, and
  loads each selected skill's complete stored knowledge bundle before
  tailoring one coherent answer to the niche.
- Regression-tests six representative multi-skill routes so offer-plus-Meta,
  B2B, ecommerce, local-service, unproven-idea, and promise-to-operations work
  cannot silently collapse back to a single framework.
- Keeps every stored marketing, sales, persuasion, influence, positioning,
  offer, funnel, advertising, outreach, follow-up, negotiation, and closing
  method available for complete explanation, comparison, ideation, and niche
  tailoring. Labels and external-execution status add context without shrinking
  the knowledge space.
- Links all 24 skills to one complete knowledge-access invariant and scans
  active instructions, agent prompts, and imported source packs with a semantic
  regression suite rather than an exact-phrase blacklist.
- Speaks with the shared strengths of Sabri Suby and Alex Hormozi: simple but
  not shallow, direct, mechanism-led, concrete, and clear about why the issue
  matters. It never uses simplification to water down the idea.
- Keeps long-form marketing frameworks backstage and regression-tests one
  continuous buyer-belief sequence, literal customer actions, proof proximity,
  ready-buyer exits, deliberate route branches, earned CTA timing, and
  evidence-carrying visuals. Release-blocking contract and mutation checks are
  paired with manual/model prompts for ecommerce, technical B2B, and high-stakes
  countercases; they protect the instruction contract rather than claiming to
  score future model output automatically.
- Treats concept generation and convergence or real-world execution review as
  distinct outputs so neither shrinks the knowledge space.
- Routes work through nine curated consulting skills and fifteen pinned
  Founder Playbook framework lenses.
- Computes economics, states countercases, and turns approved decisions into
  durable files, templates, and experiments.
- Runs an ephemeral self-check on every engagement and can, after one-time
  project consent, turn corrections and measured outcomes into redacted,
  regression-tested local rules.
- Connects to a read-only hosted MCP route at
  `https://live-consultant.sifr.marketing/mcp`. The stable v0.6
  `start_live_consultation` and `load_live_consultant_bundle` tools make
  reviewed compatible knowledge, runtime-directive, routing, and
  implementation-logic updates available on the next consultation call in the
  same task without rewriting the installed plugin.

## Continuous learning

Live Consultant does not pretend to retrain model weights or secretly pool
customer conversations. Session self-checking is automatic. Persistent learning
is visible, project-local, and off until the user enables it. In a Codex task,
say:

```text
Use $improve-live-consultant to enable project-local learning here.
```

From a source checkout, the equivalent command is:

```bash
python3 scripts/learning_loop.py init \
  --workspace <project-root> \
  --enable-local-learning
```

Candidates do not affect later advice until they clear an evidence gate and are
promoted. Public improvement uses a separate sanitized preview, exact digest
confirmation, maintainer review, regressions, and a versioned release. The tool
contains no network submission path. Local settings, candidates, and decisions
are signed with a project-local integrity key; tasks load promoted behavior only
through the verifier's `rules` command. Repeated observations compound only when
they introduce a new project-local evidence lineage; duplicate reports from one
origin count once.

## Install

Install the public marketplace from GitHub, then install the plugin:

```bash
codex plugin marketplace add alizeidan06/live-consultant --ref main
codex plugin add live-consultant@live-consultant
```

Start a new Codex task after installation.

For a version-pinned install, replace `main` with a release tag such as
`v0.6.1`.

Users upgrading from v0.5.1 or earlier update the marketplace snapshot,
reinstall, and start one new task so Codex discovers the stable v0.6 tools:

```bash
codex plugin marketplace upgrade live-consultant
codex plugin add live-consultant@live-consultant
```

After that one-time transition, `start_live_consultation` checks the current
reviewed hosted contract at the beginning of each consultation and
`load_live_consultant_bundle` loads its complete version-pinned knowledge. A
compatible hosted knowledge, runtime-directive, routing, or
implementation-logic update is therefore picked up on the next Live Consultant
call in the same task. It does not require another reinstall or new task.

This is a next-call update, not a mid-answer hot reload. One consultation stays
pinned to one contract, knowledge, and directive digest. Material tool-schema
changes, new local skill registrations, manifest changes, and local-script
changes remain incompatible changes that require a versioned marketplace
upgrade, reinstall, and new task.

The unchanged legacy `route_consultation` and `load_knowledge_bundle` tools
remain available for older clients. If neither hosted path is available, Live
Consultant uses the complete local bundle and makes the lack of a hosted
refresh explicit. A task that never calls the hosted tools continues to use its
bundled local release.

## Provenance

- Four user-supplied business and marketing PDFs were critically synthesized;
  the Sabri Suby and King Kong sources have a dedicated complete skill pack,
  while the PDFs themselves are not stored here.
- The text snapshot from
  `https://github.com/getagentseal/founder-playbook.git` is pinned to commit
  `67f25d1852547a131cd5b6b43b2fbf44d08ed8ec`.
- See
  `skills/founder-business-consultant/references/source-provenance.md`,
  `assets/upstream-founder-playbook-manifest.json`, and
  `THIRD_PARTY_NOTICES.md` for complete source and coverage details.

## Independent project

Live Consultant is not affiliated with or endorsed by Sabri Suby, King Kong,
Alex Hormozi, Acquisition.com, Meta, or OpenAI. Those names identify source
material, public frameworks, platforms, or communication characteristics being
analyzed; the plugin does not impersonate any person or claim their approval.

See `THIRD_PARTY_NOTICES.md` and `LICENSE` for attribution and license scope.
