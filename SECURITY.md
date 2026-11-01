# Security policy

## Reporting a vulnerability

Please report security problems privately, not in a public issue.

1. Open the repository's **Security** tab and choose **Report a vulnerability**.
2. If you cannot use that, email **andyyaro25@gmail.com** with "EV-SIENT security" in the subject.

Say what is affected, how to reproduce it and what an attacker could do with it. This is a
one-person project, so a reply can take a few days. Please give a reasonable time for a fix before
you disclose the problem publicly.

## In scope

- The code in this repository: the model (`src/`), the planner (`platform/app/`), the build and
  deploy scripts, and the GitHub Actions workflows.
- The live sites built from it:
  - [futurecity.andyyaro.com](https://futurecity.andyyaro.com) (the study)
  - [app.futurecity.andyyaro.com](https://app.futurecity.andyyaro.com) (the planner)
  - [futurecityfellowship.andyyaro.com](https://futurecityfellowship.andyyaro.com) (the original
    website and NFC pages)

Two kinds of report matter most here:

- **The planner sending data anywhere.** It is meant to run entirely in your browser, so your
  spreadsheet never leaves your device. Any way it leaks a file, or anything read from one, is a
  serious bug.
- **Private data in the repository.** The study's real site inputs are deliberately not published
  (DEC-016, DEC-031). If you find real input values, personal contact details, credentials or
  account identifiers anywhere in the code or its history, please report it the same way.

## Please do not

- Run load tests, denial-of-service attempts or heavy automated scans against the live sites.
- Access, change or delete anything that is not yours.
- Use real personal data while testing.
- Try social engineering or phishing.

## Supported versions

Only the `main` branch and the live sites receive fixes.
