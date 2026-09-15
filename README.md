# ECS Thailand Section Annual Meeting 2026

Quarto reveal.js meeting slides for 15 September 2026, 16:00–17:00 Bangkok time, at Montien Hotel and on Zoom.

The deck follows the seven previously circulated agenda items. Election preparation remains item 5. The election itself takes place separately. No financial report is presented. Agenda 3 instead explains conditional ECS activity support, with official sources and follow-up questions. Activity figures, financial figures, candidates and meeting decisions have not been invented.

[Open the slides](https://ecs-thai.github.io/) · [Thai meeting notes and ECS funding procedure](https://ecs-thai.github.io/meeting-notes-th.html) · [Original meeting agenda](agenda.md)

## Presenting

Open [the meeting slides](https://ecs-thai.github.io/) in a browser.

เปิดลิงก์ก่อนเริ่มประชุม กด **F** เพื่อแสดงเต็มจอ ใช้ลูกศรซ้าย–ขวาเปลี่ยนสไลด์ และกด **Esc** เพื่อดูภาพรวม สามารถสแกน QR ในสไลด์ลงทะเบียนได้ทันที รายชื่อผู้ลงทะเบียนยังเก็บใน Notion ส่วนตัวของผู้จัดประชุม

ไฟล์ `index.html` เปิดจากเครื่องได้สำหรับการนำเสนอสำรองโดยไม่ต้องต่ออินเทอร์เน็ต ส่วนการส่งแบบฟอร์มลงทะเบียนต้องใช้อินเทอร์เน็ต

- **Right / Space**: next slide
- **Left**: previous slide
- **F**: full screen, subject to browser support
- **Esc**: slide overview
- **S**: speaker view, which the browser may open in another window

Speaker notes are part of the public HTML. They contain meeting prompts, not private records.

## Voting preview

[Open the voting preview](https://ecs-thai.github.io/vote-demo.html). The slides contain its QR code and clickable link.

หน้าตัวอย่างใช้ผู้สมัครสมมติ ทดลองเลือก ตรวจทาน และกดส่งจำลองได้ ไม่มีการส่งหรือบันทึกคะแนน และยังไม่ใช่หน้าลงคะแนนจริง

The preview runs entirely in the browser, without an election backend, voter identity checks or one-time-token validation. Its selections exist only in memory and are cleared on restart or reload. Hosting providers may maintain ordinary access logs; this demo does not submit ballot choices.

## Editing

Install [Quarto](https://quarto.org/docs/download/). This project uses Quarto 1.10.18 and the built-in reveal.js format.

Edit `meeting-notes-th.qmd` for the Thai meeting brief. Edit `index.qmd` for slide content and `theme.scss` for presentation styling, then run:

```sh
quarto render
```

The results are `published/index.html` and `published/meeting-notes-th.html`. It embeds the presentation's styles, scripts and QR image. Copy both generated HTML files to the repository root to update the branch-based GitHub Pages site. Do not edit the generated HTML as the source.

The source can also be rendered with `quarto preview` for local editing.

## Registration and data

The public registration link appears in the slides. The organizer's Notion database keeps participant details privately and stores the event reference and registration time. Future-contact consent is optional. Check the submitted names against actual attendance and the separate eligible-voter list where relevant.

Do not add participant emails, private Notion exports, voting credentials, Zoom access credentials or administrator keys to this public repository.

## Sources

- The Chair's previously circulated agenda and corrected meeting time.
- [ECS Thailand Section Bylaws approved 30 May 2024](https://www.electrochem.org/wp-content/uploads/2024/07/2024-05-30-ECS-Thailand-Section-Bylaws.pdf).
- [Quarto reveal.js documentation](https://quarto.org/docs/presentations/revealjs/).
- [Quarto GitHub Pages documentation](https://quarto.org/docs/publishing/github-pages.html).
