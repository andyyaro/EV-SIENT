# Public Website Status

The Future City Fellowship GMU public website is available at:

```text
https://futurecityfellowship.andyyaro.com
```

## Public pages

The current public presentation layer includes:

- landing page;
- dashboard page;
- results page;
- methodology page;
- AI Assistant page for approved users.

## Relationship between website and repository

The website presents the project publicly. The repository documents and reproduces the model workflow.

The deployed website HTML files may be maintained separately from this branch. When website content and repository documentation diverge, update the repository documentation and website content together so the public presentation, assistant answers, and reproducible workflow remain consistent.

## Assistant limitations information

The AI Assistant page includes a user-facing model limitations information button. The content shown there should stay consistent with:

```text
docs/MODEL_LIMITATIONS.md
```

## Documentation priority

For project/model questions, the repository documentation should remain the source of truth. The public website should be treated as the presentation layer built from the project story, results, and methodology.

## Maintenance note

Avoid placing private deployment details, credentials, internal architecture notes, or operational secrets in assistant-readable project documentation. Keep public-facing project explanations separate from private maintainer notes.
