# Live Consultant

Live Consultant turns Codex into a direct, practical business consultant for
founders, entrepreneurs, startup teams, and operators.

It diagnoses the real bottleneck, builds bold offers, maps funnels, plans Meta
experiments, tests business ideas, computes unit economics, strengthens sales
and operations, and explains the next move in plain language.

## Install

Install the public marketplace and then the plugin:

```bash
codex plugin marketplace add alizeidan06/live-consultant --ref main
codex plugin add live-consultant@live-consultant
```

Start a new Codex task after installation. For a reproducible install, replace
`main` with a published tag such as `v0.1.0`.

## What is included

- Seven integrated consulting skills covering diagnosis, validation, offers and
  funnels, Meta ads, decisions, operations, and engagement leadership.
- Fifteen namespaced Founder Playbook lenses for positioning, customer
  development, pricing, sales, influence, acquisition, and experimentation.
- Reusable templates for business context, offers, funnels, economics,
  evidence, experiments, creative tests, decisions, and launch gates.
- Local scripts for workspace setup, unit-economics calculations, and source
  coverage verification.

## Try it

- `Diagnose the real bottleneck in my business.`
- `Create three bold offers for this audience and explain why they hit.`
- `Audit this funnel, calculate the economics, and give me the strongest next move.`

Live Consultant separates two jobs that are often mixed together. The creative
pass pursues the strongest desirable outcome and offer without weakening it.
When the user moves toward execution, a separate convergence pass can test the
proof, economics, capability, current requirements, and implementation path.

## Communication standard

Answers lead with the core truth, make the stakes tangible, explain the
mechanism, use numbers or concrete examples, and end with a clear move. The
style draws from direct-response clarity without pretending to be or copying
any named marketer.

## Sources and attribution

The plugin includes a sanitized text derivative of AgentSeal's MIT-licensed
Founder Playbook pinned to commit
`67f25d1852547a131cd5b6b43b2fbf44d08ed8ec`. Its original license is bundled;
long attributed quotations, community-post reproductions, artwork, and the
upstream packaging README are omitted from the public package.

Four marketing PDFs informed original, page-located critical summaries. The
PDFs, OCR dumps, worksheets, source artwork, and long passages are not included.
See `plugins/live-consultant/THIRD_PARTY_NOTICES.md` for full attribution and
license scope.

## Verify the package

```bash
python3 scripts/validate_release.py
```

The validator checks marketplace and plugin manifests, skill entry points,
local links, source coverage, script compilation, forbidden private paths,
secret signatures, symlinks, and disallowed binary/source-document files.

## Independent project

Live Consultant is an independent project by Ali Zeidan. It is not affiliated
with or endorsed by Sabri Suby, King Kong, Alex Hormozi, Acquisition.com, Meta,
OpenAI, or the authors and publishers represented in its source analysis.

Live Consultant's original work is released under the MIT License. Bundled
third-party material remains governed by its included license and notices.
