# ECS Thailand Section: nomination and candidate workflow

หน้าเว็บภาษาไทย/อังกฤษอยู่ที่ `https://ecs-thai.github.io/section-election/` รุ่นนี้ปิดรับข้อมูลจริง (`nominationsOpen: false`, `apiBase: ""`) และไม่มีผู้สมัครจริง หน้า ballot.html แสดงเฉพาะข้อมูลที่อนุมัติแล้วและเป็นตัวอย่างบัตร ไม่ส่งคะแนน ส่วน vote-demo.html เดิมยังคงอยู่

## ขั้นตอน

1. เสนอชื่อบุคคลอื่นหรือสมัครด้วยตนเอง พร้อมเลือกตำแหน่ง
2. ผู้จัดติดต่อผู้ถูกเสนอชื่อ การเสนอชื่อยังไม่ถือว่าเจ้าตัวยินยอมสมัคร
3. ส่งลิงก์ส่วนตัวให้ผู้สมัครเลือกตำแหน่ง ส่งรูปและประวัติ และยืนยันความยินยอม
4. กรรมการสรรหาตรวจคุณสมบัติและความยินยอม แล้วผู้ดูแลบันทึก shortlist
5. คณะกรรมการบริหารเห็นชอบ แล้วผู้ดูแลบันทึก approve ก่อนประกาศ

การตรวจเป็นคำสั่งสำหรับผู้ดูแลที่เข้าถึงเครื่องบริการได้ ยังไม่มีหน้าเว็บเข้าสู่ระบบสำหรับกรรมการ การแก้ประวัติจะยกเลิกทั้งสองสถานะ ต้องตรวจใหม่ และต้องส่งออกประกาศใหม่เพื่อปรับหน้าเว็บที่เผยแพร่ไปแล้ว

ตำแหน่งอ้างอิงบัตรเดิม: Chair, Vice Chair, Secretary, Treasurer และ Members-at-Large ซึ่งใช้ Yes/No/Abstain แยกคน ต้องยืนยันกติกาผู้ได้รับเลือกและวันเปิดปิดก่อนเลือกตั้งจริง ไม่มีการประกาศผู้ชนะอัตโนมัติ

## เปิดบริการรับข้อมูล

GitHub Pages ให้บริการเฉพาะหน้าเว็บ ต้องติดตั้งบริการใน backend บนเครื่องที่เปิด HTTPS และมีพื้นที่ข้อมูลส่วนตัวนอกเว็บไซต์ก่อนเปิดรับจริง ฐานข้อมูล Section ต้องแยกจาก Student Chapter ห้ามใช้ไฟล์เดียวกัน

คำสั่งด้านล่างรันจากโฟลเดอร์ section-election เปลี่ยนตำแหน่งไฟล์ส่วนตัวตามเครื่องจริง ติดตั้ง Pillow ตาม backend/requirements.txt ด้วย uv ก่อนเริ่ม

```sh
mkdir -p "$HOME/ecs-section-private"
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-section-private/section.db" init --config config.json
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-section-private/section.db" serve --origin https://ecs-thai.github.io --port 8767
```

วางบริการหลัง HTTPS proxy โดยไม่เปิดพอร์ตภายในต่อสาธารณะโดยตรง สำรองฐานข้อมูลส่วนตัว จำกัดสิทธิ์เครื่อง และทดสอบการรับส่งบนบริการจริงก่อนเปิด เปลี่ยน apiBase ใน config.json เป็น URL ของบริการ และเปิด nominationsOpen ในหน้าเว็บเมื่อพร้อม พร้อมเปิดในฐานข้อมูลด้วย:

```sh
"$HOME/.venvs/research/bin/python" backend/nominations.py --db "$HOME/ecs-section-private/section.db" intake --open
```

ปิดรับด้วย intake --close และเปลี่ยน nominationsOpen ของหน้าเว็บเป็น false การแก้ config.json หลัง init ไม่เปลี่ยนค่าที่เก็บในฐานข้อมูล

## เชิญและตรวจผู้สมัคร

ใช้ export-requests ส่งออกการเสนอชื่อเป็น CSV ส่วนตัว ตรวจรายชื่อก่อนสร้างไฟล์ name,email ตาม templates/candidates.csv แล้วสร้างลิงก์เชิญ ผู้สมัครเลือกตำแหน่งในแบบฟอร์มเอง:

```sh
"$HOME/.venvs/research/bin/python" backend/nominations.py --db "$HOME/ecs-section-private/section.db" export-requests --output "$HOME/ecs-section-private/requests.csv"
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-section-private/section.db" invite --roster "$HOME/ecs-section-private/candidates.csv" --output "$HOME/ecs-section-private/links.csv"
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-section-private/section.db" export --output "$HOME/ecs-section-private/review"
```

prepare_mail.py สร้างเพียงร่างอีเมล .eml ไม่ส่งอีเมลเอง ดู --help สำหรับพารามิเตอร์ ลิงก์เชิญเป็นข้อมูลส่วนตัว ผู้สมัครอัปโหลด JPEG/PNG ไม่เกิน 5 MB ระบบปรับขนาดและลบ metadata ของภาพ

หลังกรรมการตรวจแล้ว ใช้ candidate ID จากไฟล์ตรวจ แทน ID ด้านล่าง:

```sh
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-section-private/section.db" shortlist --id ID --eligibility-and-consent-checked
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-section-private/section.db" approve --id ID
"$HOME/.venvs/research/bin/python" backend/nominations.py --db "$HOME/ecs-section-private/section.db" publish --output "$HOME/ecs-section-private/approved-release"
```

publish ส่งออกเฉพาะผู้ผ่านทั้งสองขั้นเป็น approved.json และ photos/ ไม่มีอีเมลหรือลิงก์เชิญ ตรวจแล้วจึงนำไฟล์สาธารณะชุดนี้แทนไฟล์ใน section-election และเผยแพร่ GitHub Pages ต้องใช้โฟลเดอร์ส่งออกใหม่แต่ละครั้ง ไม่คัดลอกฐานข้อมูล ไฟล์ review รายชื่ออีเมล หรือ links.csv เข้าเว็บไซต์

## ตรวจสอบ

```sh
cd backend
"$HOME/.venvs/research/bin/python" -m unittest test_section -v
```

ทดสอบการปิดรับเสนอชื่อ การตรวจสองขั้น การยกเลิกอนุมัติเมื่อแก้ประวัติ การไม่ส่งข้อมูลส่วนตัวออกสาธารณะ และการรับคะแนน Members-at-Large ในบริการจำลอง บริการคะแนนที่เตรียมไว้ยังไม่ได้เชื่อมกับหน้า ballot.html และยังไม่ใช่การเลือกตั้งจริง

## Hosting decision: Cloudflare

ใช้ Cloudflare Workers + D1 + R2 เป็นแนวทางติดตั้งที่เลือก ดู [DEPLOY.md](DEPLOY.md) สำหรับขั้นตอนและสถานะล่าสุด ส่วน backend Python ด้านบนยังใช้สำหรับงานผู้ดูแลและอ้างอิง ไม่ต้องเปิดบริการ Render ส่วนบัญชี Cloudflare และการทดสอบบนบริการจริงยังต้องดำเนินการก่อนเปิดรับข้อมูล
