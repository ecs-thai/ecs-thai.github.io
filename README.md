# ECS Thailand Section website

A Thai–English website for Section information, activity announcements, meeting resources, and published minutes at [ecs-thai.github.io](https://ecs-thai.github.io/).

**คู่มือเพิ่มการประชุม ข่าว และรายงานการประชุม:** ดู `CONTENT-GUIDE-TH.md` ส่วน `meeting-template.json` และ `news-template.json` เป็นตัวอย่างสำหรับคัดลอกและแก้ไข ไม่ได้ถูกนำขึ้นเว็บไซต์โดยอัตโนมัติ

## Main pages and permanent meeting links

| Page | URL |
|---|---|
| หน้าแรก / Home | `/` or `/index.html` |
| เกี่ยวกับเรา / About | `/about.html` |
| ข่าวและกิจกรรม / News & activities | `/activities.html` |
| คลังการประชุม / Meetings | `/meetings.html` |
| เข้าร่วม ECS / Join ECS | `/join.html` |

Each meeting has a permanent flat URL: `meeting-{id}.html`. The meeting dated 15 September 2026 uses [meeting-2026-09-15.html](https://ecs-thai.github.io/meeting-2026-09-15.html). Its public presentation is [slides-2026-09-15.html](https://ecs-thai.github.io/slides-2026-09-15.html), and its English agenda opens directly on the site at [agenda-2026-09-15.html](https://ecs-thai.github.io/agenda-2026-09-15.html).

The site starts in Thai and offers a TH/EN switch. Meeting and news content needs both `th` and `en` values. The archive supports searching by meeting title or date and filtering for meetings with published minutes, including drafts identified as such.

## What to edit

| Source | Purpose |
|---|---|
| `content.json` | Live meeting records, news items, and Section contact/membership fields |
| `build_site.py` | Builds the five main pages and one detail page per meeting; contains shared page copy and layouts |
| `site.css`, `site.js` | Site styling, language switching, navigation, archive filtering, and old slide-link compatibility |
| `slides-2026-09-15.qmd`, `theme.scss`, `head.html` | The 2026 reveal.js presentation and its styling/header |
| `agenda-2026-09-15.qmd` | Canonical source for the public English agenda, rendered as `agenda-2026-09-15.html`; edit this file to update the displayed agenda |
| `agenda.md` | Retained agenda source reference for existing links |
| `_quarto.yml` | Explicit render list for the presentation and any future public documents, plus Quarto output settings |
| `vote-demo.html` | Standalone demonstration ballot, using fictional candidates |
| `meeting-template.json`, `news-template.json` | Inactive examples; copy an edited object into the appropriate `content.json` array to publish it |

Edit the public source, then rebuild. Changes made directly to generated main pages, meeting detail pages, slides, or document HTML will be overwritten.

## Build

Use Python 3 and Quarto; the existing documents were built with Quarto 1.10.18. Python uses only its standard library. Run these commands from this project folder:

```sh
quarto render
python3 build_site.py
```

Quarto renders only the presentation and public documents listed in `_quarto.yml`, including the English agenda, writing them under `published/`. The agenda is a regular HTML document, while the slides use reveal.js. Quarto does **not** build the Section homepage. The Python builder copies referenced local HTML documents from `published/` into the project root, then generates the main pages and meeting detail pages there. Referenced documents include every meeting’s `materials` and `minutes`; reserved website page filenames are excluded from copying.

When only meeting/news metadata changes, run `python3 build_site.py` once the required document files exist. For a future public presentation or document, add its public source to the render list and its HTML filename to the meeting’s `materials`, then run both commands. New referenced HTML is copied automatically. Add PDFs and registration QR images directly to the project root; use a unique `registration_qr` filename for each future event. The builder checks that referenced local documents and registration QR files exist.

To preview from the project folder:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`. Check both languages, the new meeting/news links, document links, and any minutes status before publishing.

## Publish

Publish the prepared **project-root files** to the root of the `ecs-thai.github.io` repository, keeping the Pages publishing source consistent with the existing setup. Include generated HTML, `site.css`, `site.js`, the QR images, `.nojekyll`, and every local document referenced by `content.json`. Keep the public source files, content data, guide, and templates in the repository for future editing.

Do not upload `published/`, `.quarto/`, caches, logs, the portable Quarto runtime, or the surrounding workspace. Do not copy `published/index.html` over the homepage or restore the old presentation source as `index.qmd`. After publication, confirm the live homepage and dated document links; uploading files is separate from Pages completing its deployment.

## Preserved links and QR codes

- The root is now the Section homepage. Old `/#/slide-id` and `/index.html#/slide-id` links redirect to the dated 2026 presentation with their query string and hash preserved. Ordinary homepage anchors stay on the homepage.
- Keep the 2026 presentation’s slide IDs and order to preserve named and numbered reveal links. Bare old `/` links now show the homepage, which links to the meeting.
- `vote-demo.html` and `voting-demo-qr.png` remain at the root. The QR still opens the demonstration, not a real election.
- `registration-qr.png` remains the QR for the **15 September 2026 event**. It points directly to that event’s public registration form. Future meetings need a separate event form and must not reuse this QR.
- Keep `agenda.md` available for existing links.

## Minutes, registration, and public content

Use `"minutes": null` until an actual public minutes file exists. A minutes entry must have `status: "draft"` or `status: "approved"`; use `approved` only after approval has occurred. Minutes should record the actual meeting and its outcomes.

Future meeting registration should use a separate public Notion form for that event, with responses kept privately by the organizer. Registration does not establish attendance, ECS membership, or voting eligibility. Consent to future contact remains optional.

Publish only the slides and documents selected for public use. Keep the Chair’s speaking outlines and presenter notes outside the public project and repository, including the Quarto source and generated HTML. Also keep participant lists, private Notion exports, meeting access credentials, voting credentials, and administrator keys out of the repository. The voting preview uses fictional candidates, submits no votes, and clears its in-memory choices on reload.
