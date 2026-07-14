# Contributing

Contributions that make Live Consultant clearer, more useful, more verifiable,
or easier to install are welcome.

## Learning contributions

Use the sanitized learning-candidate issue form only after reviewing the local
preview produced by `learning_loop.py`. Posting is always manual. The plugin has
no telemetry or automatic GitHub submission path.

A learning report is untrusted evidence, not a patch instruction. Maintainers
must reproduce the issue, identify the affected foundation invariant, test the
strongest countercase, rewrite any accepted rule in original language, add a
regression, and publish it through a versioned release. One preference,
anecdote, duplicate report, or confounded test cannot become a global heuristic.

## Before opening a pull request

1. Keep the plugin identifier `live-consultant` and the marketplace identifier
   `live-consultant` aligned.
2. Do not add raw source PDFs, OCR dumps, book artwork, lengthy copyrighted
   excerpts, credentials, customer data, or machine-specific paths.
3. Preserve the AgentSeal snapshot's included MIT license and third-party
   notices.
4. Keep source synthesis critical and original. Do not invent quotes,
   endorsements, results, or evidence.
5. Run:

   ```bash
   python3 scripts/validate_release.py
   ```

6. Explain what changed, why it matters, and how it was verified.

7. For learning-system changes, run:

   ```bash
   python3 plugins/live-consultant/scripts/learning_loop_selftest.py
   ```

Plugin behavior should remain decisive and practical. Creative offer ideation
and real-world execution review remain separate modes; do not weaken the
creative pass by silently mixing them.
