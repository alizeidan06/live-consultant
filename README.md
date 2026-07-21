# Live Consultant

Live Consultant turns Codex into a direct, practical business consultant for
founders, entrepreneurs, startup teams, and operators.

It diagnoses the real bottleneck, builds bold offers, maps funnels, plans Meta
experiments, tests business ideas, computes unit economics, strengthens sales
and operations, and explains the next move in plain language. Before it does
that, it resolves the exact buyer, trigger, business model, geography, channel,
and stage so the research and answer fit the real niche.

## Install

Install the public marketplace and then the plugin:

```bash
codex plugin marketplace add alizeidan06/live-consultant --ref main
codex plugin add live-consultant@live-consultant
```

Start a new Codex task after installation. For a reproducible install, replace
`main` with a published tag such as `v0.6.0`.

## Get future releases

Live Consultant v0.6 establishes a permanent hosted contract. Users upgrading
from v0.5.1 or earlier must upgrade the marketplace snapshot, reinstall the
plugin, and start one new Codex task so Codex can discover the stable v0.6 tool
schemas. New users likewise start one task after their initial installation.

After that transition, a v0.6-compatible task starts each consultation through
`start_live_consultation` and reads its complete version-pinned bundle through
`load_live_consultant_bundle`. Reviewed compatible hosted knowledge, runtime
directives, routing, and implementation-logic updates at
`https://live-consultant.sifr.marketing/mcp` are used on the next Live
Consultant call in that same task. The user does not reinstall the plugin or
open another task for those compatible updates.

The update boundary is deliberate:

1. **Compatible hosted updates:** arrive on the next consultation start in the
   same v0.6-compatible task. One answer remains pinned to one contract,
   knowledge, and runtime-directive digest, so an update does not rewrite an
   answer while it is being produced.
2. **Incompatible contract or bundled changes:** a material tool-schema change,
   new local skill registration, manifest change, or local-script change still
   requires a versioned marketplace upgrade, reinstall, and new Codex task.
3. **Fallbacks:** older tasks can continue through the unchanged legacy
   `route_consultation` and `load_knowledge_bundle` tools. If hosted access is
   absent or unavailable, the plugin uses its complete bundled knowledge pack
   and reports that it did not receive a hosted refresh.

New installations from `main` see the latest bundled release. Existing users
refresh bundled plugin files with:

```bash
codex plugin marketplace upgrade live-consultant
codex plugin add live-consultant@live-consultant
```

Start a new Codex task after this v0.6 transition or any later incompatible
bundled release. Once a task has the stable v0.6 tools, reviewed compatible
hosted updates do not require another task.

Every public update is exported from reviewed private `main`, validated in both
repositories, merged through a protected public pull request, and published as
an immutable version tag and GitHub release. A failed gate leaves the last good
release in place.

The hosted production service also requires a strong
`LIVE_CONSULTANT_TOKEN_SECRET` of at least 32 UTF-8 bytes in Deno environment
settings. It authenticates stateless consultation identifiers and cursors. It
must never be committed or returned to a client; missing or short configuration
makes `/healthz` and the v0.6 consultation tools fail closed.

## What is included

- Nine integrated consulting skills covering the complete Sell Like Crazy
  system, diagnosis, validation, offers and funnels, Meta ads, decisions,
  operations, engagement leadership, and continuous improvement.
- Fifteen namespaced Founder Playbook lenses for positioning, customer
  development, pricing, sales, influence, acquisition, and experimentation.
- Reusable templates for business context, offers, funnels, economics,
  evidence, experiments, creative tests, decisions, and launch gates.
- Local scripts for workspace setup, unit-economics calculations, source
  coverage and foundation verification, and privacy-preserving learning.
- A universal niche-intelligence protocol and reusable niche context card.
- A machine-verified skill assembly protocol and complete knowledge manifest.
- A universal complete knowledge-access invariant and semantic regression
  verifier covering active instructions, agent prompts, and bundled sources.
- Six release-tested multi-skill routing fixtures covering common consulting
  systems from offer-plus-Meta through promise-driven operations repair.
- A read-only hosted MCP service with stable consultation-start and bundle-load
  tools, version-pinned answers, unchanged legacy fallbacks, and centrally
  reviewed compatible knowledge, directive, routing, and logic updates.

## Niche intelligence

Live Consultant infers the buyer, payer, trigger, offer, business model,
geography, channel, stage, and current phase from the request and project
artifacts before asking questions. If the niche is already clear, it proceeds.
If one unknown could change the answer, it asks the single most useful question
and still gives provisional analysis whenever a reversible assumption is safe.

Research is scoped to the exact niche and decision. Project ground truth comes
first, followed by direct market artifacts and current authoritative sources
matched to the claim. Evidence from one buyer, geography, channel, period,
price context, or business model is not silently transferred to another. The
niche layer changes how the foundation is applied; it does not rewrite the
foundation.

## Complete skill assembly

Live Consultant first identifies the outcome the human needs, decomposes it
into capabilities, and selects every skill with a distinct contribution. It
then loads the complete framework, cases, examples, integrations, and source
notes declared for each selected skill before tailoring one answer to the
niche. Directly invoking a specialist does not bypass this assembly step.

The release includes a first-class `$sell-like-crazy` skill covering Dream
Buyer and Halo research, the Larger Market Formula, HVCOs, opt-in capture,
Godfather Offers, the 17-step sales message, traffic economics, Magic Lantern
nurture, doctor-style sales conversion, and email automation.

Every stored marketing, sales, persuasion, influence, positioning, offer,
funnel, advertising, outreach, follow-up, negotiation, and closing method stays
available for complete explanation, comparison, ideation, and niche tailoring.
Ethical, manipulative, artificial, aggressive, risky, legal, policy,
compliance, platform, and similar labels are context to analyze rather than
knowledge controls. Imported categorical commands become source positions and
performance hypotheses with all variants and consequences preserved.

Truth status, evidence quality, account access, authorization, and execution
readiness remain explicit and separate. They govern factual assertions and
external actions without shrinking the knowledge or creative space.

## Continuous learning

Every Live Consultant answer runs an ephemeral self-check. Persistent learning
is off until the user explicitly enables it for a selected project. In Codex,
say:

```text
Use $improve-live-consultant to enable project-local learning here.
```

From a repository checkout, the equivalent command is:

```bash
python3 plugins/live-consultant/scripts/learning_loop.py init \
  --workspace <project-root> \
  --enable-local-learning
```

After that opt-in, explicit corrections, caught mistakes, measured outcomes,
and repeated routing failures can become redacted candidates. Candidates affect
future advice only after evidence review, a countercase, and a regression test.
They stay inside that project and are ignored by Git by default.

The local store signs settings, candidates, and decisions with a project-local
integrity key. Runtime tasks use the verifier's `rules` command, so directly
editing the rendered rule file does not change trusted behavior.
Repeated observations append through project-local evidence lineage IDs; one
experiment, artifact, cohort, or report counts once even when reworded.

Community improvement is also opt-in. The local learning tool can prepare a
sanitized preview and exact digest, but it cannot submit to GitHub or upload
the preview. Hosted consultation tools process only the arguments explicitly
sent to them and do not turn calls into learning candidates. Read [the learning
policy](LEARNING_POLICY.md) for the full lifecycle.

## Try it

- `Diagnose the real bottleneck in my business.`
- `Create three bold offers for this audience and explain why they hit.`
- `Audit this funnel, calculate the economics, and give me the strongest next move.`
- `Infer my exact niche, research it, and ask only what could change your answer.`
- `Use $sell-like-crazy to build my complete Dream Buyer-to-sale system.`
- `Use $improve-live-consultant to turn this correction into a tested local rule.`

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

Four marketing PDFs informed original, page-located structured synthesis. The
Sabri Suby and King Kong sources now power a dedicated framework, case,
example, integration, and source-map pack. The PDFs, OCR dumps, worksheets,
source artwork, and long passages are not included.
See `plugins/live-consultant/THIRD_PARTY_NOTICES.md` for full attribution and
license scope.

## Verify the package

```bash
node --version  # requires Node 20.9 or newer
npm ci --ignore-scripts --no-audit --no-fund
npm run check
python3 scripts/validate_release.py
```

Together these commands run the hosted runtime contract tests and production
build, then validate marketplace, plugin, and MCP manifests, the hosted tool
schema, skill entry points,
complete knowledge-bundle assembly, the Sell Like Crazy source pack, local
links, routing fixtures, source coverage, script compilation, the complete learning-loop
self-test, 21 destructive mutation regressions, forbidden private paths,
secret signatures, symlinks, and disallowed
binary/source-document files.

## Policies and support

- [Privacy](PRIVACY.md)
- [Terms](TERMS.md)
- [User support and bug reports](https://github.com/alizeidan06/live-consultant/issues)
- [Security reporting](SECURITY.md)
- [Learning policy](LEARNING_POLICY.md)
- [OpenAI reviewer test packet](OPENAI_REVIEW.md)

## Independent project

Live Consultant is an independent project by Ali Zeidan. It is not affiliated
with or endorsed by Sabri Suby, King Kong, Alex Hormozi, Acquisition.com, Meta,
OpenAI, or the authors and publishers represented in its source analysis.

Live Consultant's original work is released under the MIT License. Bundled
third-party material remains governed by its included license and notices.
