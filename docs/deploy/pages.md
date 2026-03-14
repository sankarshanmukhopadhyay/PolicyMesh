# GitHub Pages deployment

This repository publishes documentation from `docs/` using GitHub Actions.

## Enablement steps

1. Push the repository with `.github/workflows/pages.yml` present on `main`.
2. In GitHub repository settings, set **Pages** to use **GitHub Actions** as the source.
3. Ensure Actions are permitted to deploy Pages in repository settings.
4. Merge to `main` to trigger a deployment.

## What gets published

The Pages workflow copies the contents of `docs/` into the deployment artifact. The landing page is `docs/index.md`.

## Operational note

This is documentation publishing, not application hosting. Keep production PolicyMesh nodes behind a proper TLS terminator and do not use GitHub Pages for sensitive runtime surfaces.
