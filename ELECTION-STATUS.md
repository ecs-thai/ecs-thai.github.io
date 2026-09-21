# ECS election systems: handoff and status

Updated: 22 September 2026 (Asia/Bangkok).

## User decisions to preserve

- Use GitHub ecs-thai and Cloudflare; avoid fixed monthly hosting charges. Stay within free allowances and monitor R2 overages.
- Do not generate or email real three-character voting codes until Soorathep explicitly requests it.
- Student Chapter: Chulalongkorn University Student Chapter.
- Student offices: President, Vice President, Secretary, Treasurer.
- Each eligible student receives a three-character code by email later; voting uses registered email plus code, once per voter.
- Real candidate names, eligible student names/emails, and election dates have not been supplied.
- Candidates select their office and submit a photo, biography, and publication consent through a private invitation link.
- Profile invitation links and operator credentials are long secrets, separate from voting codes.
- Do not alter the existing Section voting Workers.

## ECS Thailand Section: completed and live

- Public nominations: https://ecs-thai.github.io/section-election/
- API: https://ecs-section-candidates.ecs-thailand-election.workers.dev
- D1 and private R2 installed. Nominations open. Production had zero candidate/nomination records when verified.
- Personal profile links, office selection, photo/biography intake, consent, private storage, image sanitization, review and publication are implemented.
- Nominating Committee review followed by Executive Committee approval; administrator records their decisions using the private operator tool.
- Editing a candidate profile removes its approval/publication until reviewed again.
- Isolated live staging tests passed including a 3.8 MB photo.
- Voting preview is still a preview. Integration with existing Section voting is not claimed complete.
- Operator instructions: section-election/DEPLOY.md.

## Student Chapter: implemented and deployed

- Separate production Worker deployed: https://ecs-student-election.ecs-thailand-election.workers.dev
- D1 ecs-student-election and private R2 ecs-student-photos created; both schema migrations applied.
- Production operator and credential-hashing secrets installed outside Git.
- Implemented nomination form, candidate intake, office selection, sanitized image publication and organizer approval.
- Implemented scheduled voting with frozen candidates, HMAC-protected credentials, five-failure lockout, atomic once-only ballot recording, safe retries, and results after closing.
- Local integration passed: nomination, photo, approval, schedule/profile lock, four simultaneous submissions producing one ballot, retry after closing, correct tally.
- Real voting codes have not been issued or emailed. Local tests used fixed synthetic fixtures only.
- Separate live staging checks passed: intake, photo, approval, frozen election, four simultaneous requests producing one ballot, safe retry after closing and correct tally.
- Public Student Chapter config connects the production service. Nominations are open; voting remains draft until real candidates and dates are supplied.
- Nomination page: https://ecs-thai.github.io/student-election/nominate.html
- Election page: https://ecs-thai.github.io/student-election/
- Operator instructions: student-election/cloudflare/README.md.

## Deployment verification

Local and isolated live staging checks passed. Public website deployment and browser verification are the final checks for this update.

## Later work requiring actual election information / explicit instruction

- Receive actual candidates and eligible voter roster; keep private files outside Git.
- Create and deliver candidate invitation links only when instructed; process submissions and approvals.
- Confirm election dates, eligibility and election rules, including ties.
- Schedule voting and freeze approved candidates.
- Only when explicitly requested, issue real codes, then send emails through an authorized sending method. A mail-draft tool exists; automatic email delivery is not configured.
- Monitor quota, back up D1 plus R2, decide retention and cleanup after election.
- After closing, export counts and have the organizer certify results.

## Private credentials

Operator files are under ~/ecs-section-private/ on the installation machine, mode 600. Never copy values into Git, chat, documentation or logs. Production Student files: student-admin-token and student-credential-key. Section: cloudflare-admin-token.

## Important distinction

Code written is not the same as live readiness. Report each system's deployment and tested behavior separately. Do not state that voting needs only codes until candidates, roster, schedule, deployment, and validation are all complete.
