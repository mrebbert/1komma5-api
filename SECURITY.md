# Security Policy

## Supported versions

Only the latest released version on PyPI receives fixes. Older versions
are not maintained.

| Version | Supported |
|---------|-----------|
| latest  | yes       |
| older   | no        |

## Reporting a vulnerability

Please report suspected security problems privately by email to
**code@rebbert.de**. Do not open a public GitHub issue.

A useful report includes:

- A description of the issue and its impact.
- Steps to reproduce.
- The library version (`pip show onekommafive`) and Python version.
- Any relevant log output (with credentials and personal data redacted).

You can expect an initial acknowledgement within a few days. Coordinated
disclosure timelines will be agreed case by case.

## Scope

This library handles 1KOMMA5° account credentials and OAuth tokens.
Issues that are in scope include:

- Credential or token leakage to unintended destinations.
- Authentication or token-refresh flaws.
- Insecure handling of API responses that could lead to remote code
  execution, path traversal, or similar in consumers of the library.

Out of scope:

- Issues in the upstream 1KOMMA5° / Auth0 services themselves — please
  report those to the respective vendors.
- Vulnerabilities that require an attacker to already have full control
  of the user's machine or network.
