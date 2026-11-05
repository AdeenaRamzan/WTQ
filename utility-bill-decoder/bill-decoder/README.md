# Utility Bill Decoder

Front-end only results viewer for Pakistani electricity bills (K-Electric, LESCO, IESCO). No backend, no API calls, works offline.

## Run
```
npm install
npm run dev      # local dev server
npm run build    # static files in dist/
```

## Where the data goes
- `public/data/report.json` — the report (fetched at runtime; never hardcoded).
- `public/data/images/` — bill images; each bill's `image` field is relative to `public/data/`.
- Or click **Load report.json** in the top bar to pick a file (images still load from `public/data/images/`).

If the file is missing or invalid, an empty state explains what to do.

## Theme
Colors are CSS variables at the top of `src/index.css` (`:root` for light, `.dark` for dark). Change `--bg` there to try another background. Theme choice is kept in React state only.
