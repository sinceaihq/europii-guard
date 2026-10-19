# Security Policy

## Reporting a vulnerability

**Use GitHub's private vulnerability reporting:**
**[Report a vulnerability](https://github.com/sinceaihq/europii-guard/security/advisories/new)**

If GitHub reporting is unavailable to you, email **builders@sinceai.fi**.
Please do not open a public issue for a suspected vulnerability, and never
paste real personal data into an issue.

We aim to acknowledge reports within a few working days; EuroPII Guard is
maintained by a small team and we do not promise a fixed remediation deadline.

## Scope

- **Systematic false negatives.** A class of real personal data that is
  reliably missed (e.g. a national ID format written in a common way we do
  not match). Describe the *format* with a synthetic example, not real data.
- **Crashes or catastrophic slowdowns** on crafted input (the library is
  meant to run on untrusted text).
- **Leaks through redaction**, e.g. the `hash` style revealing values.
- **Personal data in the benchmark.** Report anything that looks real.

Individual false positives or misses that are not systematic are normal
issues — please open a regular issue.
