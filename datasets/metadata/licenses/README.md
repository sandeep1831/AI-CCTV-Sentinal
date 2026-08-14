# License Records

One file per distinct license actually encountered in a dataset
source, named `<license-slug>.md` (e.g. `cc-by-4.0.md`). Each file
should capture, in plain language, what that license permits for this
project:

- Commercial use allowed?
- Redistribution allowed?
- Attribution required, and in what form?
- Any share-alike / non-commercial / no-derivatives restriction?
- Link to the canonical license text.

This directory is empty until a real dataset source is onboarded — see
`datasets/metadata/sources/SOURCE_TEMPLATE.json` and
`docs/research/dataset-gap-analysis.md`.

**Rule:** never assume a dataset found via search is free to
redistribute. If a source's license is unclear, record it as
`"Unknown — pending review"` in its `DatasetSource.license` field
(see `scripts/dataset/schemas.py`) rather than guessing.
