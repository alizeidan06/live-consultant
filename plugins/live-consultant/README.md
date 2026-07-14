# Live Consultant

Live Consultant is an independent Codex plugin by Ali Zeidan for integrated
business diagnosis, bold direct-response offer creation, market and idea
validation, sales, funnels, websites, Meta ads, analytics, operations, and
decision support.

## Core behavior

- Finds the binding constraint before recommending tactics.
- Uses the Sabri/King Kong mindset without compliance, proof, or implementation
  dilution during offer ideation.
- Speaks with the shared strengths of Sabri Suby and Alex Hormozi: simple but
  not shallow, direct, mechanism-led, concrete, and clear about why the issue
  matters. It never uses simplification to water down the idea.
- Keeps convergence and real-world execution review in a separate later pass.
- Routes work through eight curated consulting skills and fifteen pinned
  Founder Playbook framework lenses.
- Computes economics, states countercases, and turns approved decisions into
  durable files, templates, and experiments.
- Runs an ephemeral self-check on every engagement and can, after one-time
  project consent, turn corrections and measured outcomes into redacted,
  regression-tested local rules.

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
`v0.2.0`.

## Provenance

- Four user-supplied business and marketing PDFs were critically synthesized;
  the PDFs themselves are not stored here.
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
