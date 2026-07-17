# Routing map

Use the [skill assembly protocol](skill-assembly-protocol.md) and
`assets/skill-knowledge-manifest.json`. Select every skill with a distinct job;
remove only true duplication. A “primary” names the spine of the answer, not a
limit on companion knowledge.

## Need-to-skill map

| Need | Primary spine | Distinct companions to consider |
|---|---|---|
| Vague or multi-system problem | `founder-business-consultant` | `audit-business`, `reason-business-decision`, every domain skill surfaced by the issue tree |
| Idea, market, or demand proof | `validate-business-idea` | `founder-playbook-mom-test`, `founder-playbook-four-steps`, `founder-playbook-lean-startup`, offer skill to create the strongest test |
| Root-cause business audit | `audit-business` | `reason-business-decision`, the skills owning each material finding |
| Formal tradeoff or uncertainty | `reason-business-decision` | relevant domain, operations, validation, and economics skills |
| Positioning and category | `founder-playbook-obviously-awesome` | `founder-playbook-blue-ocean`, `founder-playbook-crossing-the-chasm`, `founder-playbook-storybrand` |
| Pricing and packaging | `founder-playbook-monetizing-innovation` | `founder-playbook-100m-offers`, `sell-like-crazy`, `reason-business-decision` |
| Sabri Suby, Sell Like Crazy, King Kong, Halo, Godfather, Magic Lantern, or a complete buyer-to-sale system | `sell-like-crazy` | `founder-playbook-100m-offers`, `design-offer-funnel`, `plan-meta-ads`, sales and operations skills as required |
| Bold offer | `sell-like-crazy` + `founder-playbook-100m-offers` | `founder-playbook-monetizing-innovation`, `design-offer-funnel`, `reason-business-decision` |
| Copy, page, website, or funnel artifact | `design-offer-funnel` | `sell-like-crazy`, `founder-playbook-storybrand`, `founder-playbook-made-to-stick`, `founder-playbook-influence` |
| Lead magnet or nurture | `sell-like-crazy` | `founder-playbook-100m-leads`, `founder-playbook-made-to-stick`, `founder-playbook-influence`, `build-business-operations` |
| Channel selection | `founder-playbook-traction` | `founder-playbook-100m-leads`, `sell-like-crazy`, channel specialist |
| Meta planning or audit | `plan-meta-ads` | `sell-like-crazy`, `design-offer-funnel`, `founder-playbook-100m-offers`, `reason-business-decision` |
| Transactional or short-cycle sales pressure | `sell-like-crazy` | `founder-playbook-influence`, `founder-playbook-100m-offers` |
| Complex B2B sales | `founder-playbook-spin-selling` | `sell-like-crazy`, `founder-playbook-influence`, `founder-playbook-monetizing-innovation` |
| MVP, experiment, or pivot | `founder-playbook-lean-startup` | `validate-business-idea`, `founder-playbook-mom-test`, the domain skill defining the tested artifact |
| Business setup and delivery system | `build-business-operations` | `reason-business-decision`, `audit-business`, offer or guarantee skill defining the promise |
| Correction, failed advice, measured outcome, or repeated mistake | `improve-live-consultant` | every affected domain skill, plus the original evidence and test |

## Multi-skill assembly patterns

### Offer plus Meta campaign

Load `sell-like-crazy`, `founder-playbook-100m-offers`,
`founder-playbook-100m-leads`, `plan-meta-ads`, and
`reason-business-decision`. Add `design-offer-funnel` when producing the page or
full conversion path. The Leads pack owns the paid lead-getter, lead-magnet,
follow-up, and scale mechanics; the Meta specialist owns current account,
creative-test, measurement, and platform decisions.

### B2B pricing and sales

Load `founder-playbook-monetizing-innovation`, `founder-playbook-spin-selling`,
`founder-playbook-influence`, and `sell-like-crazy`. Add
`founder-playbook-100m-leads` and `build-business-operations` when the request
includes nurture, reactivation, follow-up automation, CRM ownership, or service
levels. Operations also joins when the guarantee or package changes delivery.

### New ecommerce offer

Load `validate-business-idea`, `sell-like-crazy`,
`founder-playbook-100m-offers`, `plan-meta-ads`, and
`reason-business-decision`. Add `design-offer-funnel` for production.

### Local high-ticket service

Load `sell-like-crazy`, `founder-playbook-100m-offers`,
`founder-playbook-influence`, `founder-playbook-100m-leads`, the applicable
channel specialist, and
`build-business-operations` if speed, capacity, or guarantee fulfillment is
part of the offer.

### New idea with no proof

Load `validate-business-idea`, `founder-playbook-mom-test`,
`founder-playbook-lean-startup`, `sell-like-crazy`, and
`founder-playbook-100m-offers`. The validation skills test reality; the offer
skills ensure the market sees the strongest version rather than a timid test.

### Operations problem caused by the promise

Load `audit-business`, `build-business-operations`,
`reason-business-decision`, and the offer or sales skill that created the
customer expectation—typically `sell-like-crazy`,
`founder-playbook-100m-offers`, `design-offer-funnel`, or
`founder-playbook-spin-selling`. Do not repair fulfillment without
understanding the promise it must keep.

## Context rules

- Direct invocation of a specialist does not bypass assembly.
- The upstream Diagnose lens can suggest a starting point, but its preserved
  one-framework workflow does not override Live Consultant's active assembly
  protocol.
- Load every Markdown file beneath each selected skill's declared bundle roots
  plus every individually declared bundle file.
- Resolve conflicts by buyer, stage, sales motion, price, evidence, economics,
  and owner directives.
- Return one recommendation and execution path, not a list of framework
  summaries.

The namespaced Founder Playbook skills route to the pinned upstream snapshot.
They preserve provenance and supply complete framework packs. Live Consultant's
active skills own the final contextual synthesis and current verification.
