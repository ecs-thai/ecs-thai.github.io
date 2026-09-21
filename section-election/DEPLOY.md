# Cloudflare deployment

Selected hosting: GitHub Pages for the existing website, Workers for intake, D1 for private records, and a private R2 bucket for photos. No voting-code issuance, email sending, or ballot submission routes are exposed by this Worker.

Current status (2026-09-22): Production is deployed at https://ecs-section-candidates.ecs-thailand-election.workers.dev with the D1 migration applied and the private R2 bucket connected. The owner activated R2. Nominations are open and public config.json connects the GitHub Pages forms to this service. Voting remains in draft mode, with no voting codes generated or emails sent.

Live staging checks passed nomination intake, private photo upload, profile retrieval, two-stage approval, publication, revision protection, and automatic removal from the public feed after an edit. Staging uses a separate Worker, D1 database, and private R2 bucket configured in wrangler.staging.json; nominations there are closed. Synthetic records are confined to staging.

On the installation machine, the production operator credential is stored privately at ~/ecs-section-private/cloudflare-admin-token (mode 600), outside the repository. Do not share or commit this file. Existing election Workers are unchanged.

## Deployment after account setup

From section-election/cloudflare:

1. `wrangler login` and authorize the intended Cloudflare account.
2. `wrangler d1 create ecs-section-candidates`. Put the returned database ID in wrangler.jsonc. The ID is configuration, not a secret.
3. Enable R2 in the account and review its usage-based billing terms before checkout. Keep Workers on Free; R2 Standard has free allowances but bills overages. Create `ecs-section-candidate-photos` with `wrangler r2 bucket create ecs-section-candidate-photos`. Keep public bucket access disabled.
4. `wrangler d1 migrations apply ecs-section-candidates --remote`.
5. Generate a long admin secret in a private file outside the repository and set it with `wrangler secret put ADMIN_TOKEN`. Never place the value in source, public config, chat, or command-line arguments. This is an operator credential, not a three-character voting code.
6. `wrangler deploy`. Verify /health and /intake on the actual returned HTTPS URL.
7. Use admin.py to open nominations, then backend/activate.py to connect config.json to that actual HTTPS URL. Commit the public config only after checking the live service.
8. Run a separate staging Worker/database/bucket with synthetic data for the live end-to-end check. Keep production empty until ready for real candidates. Do not run test-local.py against production.

## Operator workflow

The administrator records committee decisions through the private admin.py tool. It is not a multi-user committee dashboard. Supply --api and --token-file before the command. Run it using "$HOME/.venvs/research/bin/python" and install Pillow as in backend/requirements.txt.

- `list --output PRIVATE_FILE`: save nominations and candidate revisions privately.
- `invite --name NAME --output PRIVATE_FILE`: create a 14-day personal profile link, save it privately. No email is sent. The user must explicitly request sending invitations later.
- After a candidate submits, note their ID and revision from list.
- `sanitize --id ID --revision N`: download the private image, decode it with Pillow, enforce pixel limits, resize it, and strip metadata before uploading a sanitized JPEG. Raw images are never published.
- `shortlist --id ID --revision N`: record Nominating Committee review after checking eligibility and consent.
- `approve --id ID --revision N`: record Executive Committee approval. This requires shortlist for the same revision. The public /approved feed immediately includes the profile and sanitized photo.
- `intake --open`: open nominations. `intake` without --open closes nominations.

Candidate edits increment the revision and reset both approvals and the public photo. Published profiles immediately disappear from /approved until reviewed again. The ballot preview fetches this feed after connection; it still does not submit votes. Candidate profile links remain valid until their 14-day expiry.

Candidate uploads undergo file-signature and size checks in the Worker. Full decoding, pixel checks, resizing, and metadata removal happen in the private sanitize step before review/publication, avoiding heavy image processing on Workers Free. Storage is private by default. Raw files and superseded images require a retention/cleanup policy once intake ends.

Back up D1 with `wrangler d1 export ecs-section-candidates --remote --output PRIVATE_FILE` and back up the private R2 objects separately. A database export alone does not contain photos. Keep copies outside GitHub. Free-tier quota limits and R2 usage should be checked during the intake period. The Worker limits requests per Cloudflare-provided client IP; nomination deduplication prevents duplicate records for the same email/office.

## Local checks

Use a private .dev.vars containing ADMIN_TOKEN (ignored by git). Apply migrations with --local and start `wrangler dev --local --port 8790`. Run "$HOME/.venvs/research/bin/python" test-local.py. It only targets 127.0.0.1 and uses synthetic names, emails, and images; it never generates voting codes or sends mail. Use `wrangler deploy --dry-run` to verify packaging without publication.
