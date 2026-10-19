---
title: EuroPII Guard
emoji: 🛡️
colorFrom: indigo
colorTo: blue
sdk: static
app_file: index.html
pinned: true
license: apache-2.0
short_description: Redact European personal data in your browser (Pyodide)
datasets:
  - sinceaihq/europii-bench
tags:
  - pii
  - privacy
  - redaction
---

# EuroPII Guard demo

Paste text and see which European personal data
[EuroPII Guard](https://github.com/sinceaihq/europii-guard) finds and how it
redacts it: national identity numbers of 22 countries, EU VAT numbers, IBANs,
payment cards, phone numbers, e-mail and IP addresses.

The Python library runs **in your browser** with
[Pyodide](https://pyodide.org); no text is sent to any server.

Privacy assistance, not a guarantee: names and addresses are not detected,
and no tool finds all personal data.

Built by [Since AI](https://sinceai.ai).
