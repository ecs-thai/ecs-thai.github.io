# Student Chapter Cloudflare service

Production: https://ecs-student-election.ecs-thailand-election.workers.dev

Separate from the Section services. D1 holds nominations, profiles, credential hashes and ballots. Private R2 holds photos. No email is sent by this Worker.

## Operator workflow

Run admin.py with the absolute interpreter "$HOME/.venvs/research/bin/python", supplying --api with the production URL and --token-file "$HOME/ecs-section-private/student-admin-token" before the subcommand.

1. `intake --open` enables nominations; `intake` closes them.
2. `list --output PRIVATE_FILE` exports private nominations and candidate revisions outside Git.
3. `invite --name NAME --output PRIVATE_FILE` creates a personal 14-day profile link. Send only with explicit authorization. This is not a voting code.
4. After submission, `sanitize --id ID --revision N`, then `approve --id ID --revision N` record organizer approval. Sanitization decodes/resizes the private image and strips metadata. Shortlisting is optional for this chapter.
5. Candidate edits remove approval until reviewed again.
6. Once every office has approved candidates and dates are confirmed, `schedule --opens-at ISO_DATE --closes-at ISO_DATE` freezes profiles and nominations. Dates require timezones. Scheduling is intentionally one-time; there is no public reset route.
7. Only on explicit instruction, run issue.py with --api, --token-file, --roster PRIVATE_CSV and --output PRIVATE_CODES_CSV. Roster columns: name,email. After interruption use --resume with the same output file. Registration is idempotent for the same email/code and refuses replacement credentials. Complete before voting opens.
8. backend/prepare_mail.py prepares private email drafts. Automatic delivery is not configured; sending requires explicit authorization.
9. `unlock --email EMAIL` resets a five-failure lockout after organizer verification.
10. `results --output PRIVATE_FILE` exports counts after closing. Apply chapter rules to ties and certify results separately.

The frontend retrieves election state from /election. Scheduling takes effect without editing public config. Atomic SQL and a trigger enforce one ballot despite simultaneous submissions. Retries return the original receipt even after closing. Ballots contain no voter identity field; database administrators retain privileged access. Do not claim cryptographic anonymity or independent certification.

## Deployment and checks

wrangler.jsonc is production; wrangler.staging.json isolates testing. Apply migrations, deploy, and install ADMIN_TOKEN and CREDENTIAL_KEY as secrets. Keep Workers Free; R2 overages are billable. Never put secrets in Git, chat or logs.

Local checks use a fresh local database, ignored .dev.vars, wrangler dev --local --port 8791, and test-local.py. Fixtures are fixed, synthetic and localhost-only. Live checks must target only isolated staging resources with its private operator token.

Back up D1 and private R2 separately outside Git. Decide retention after the election. Current status and outstanding inputs: ../../ELECTION-STATUS.md.
