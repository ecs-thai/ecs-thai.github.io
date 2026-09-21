# Live hosting

Cloudflare replaces the optional local Python server for production. See [operator instructions](cloudflare/README.md) and [current status](../ELECTION-STATUS.md). Instructions below describe the original local backend. Do not issue real codes until explicitly authorized.

# Chulalongkorn University Student Chapter election

หน้าเว็บ: https://ecs-thai.github.io/student-election/

## สถานะปัจจุบัน

ยังไม่เปิดลงคะแนน ไม่มีผู้สมัครจริง และยังไม่กำหนดวันเลือกตั้ง หน้าเว็บแสดง 4 ตำแหน่ง ตำแหน่งละ 1 คน: President, Vice President, Secretary, Treasurer ปุ่มทดลองโหลดผู้สมัครสมมติจาก `sample.json` โดยไม่ส่งหรือบันทึกคะแนน รองรับไทยและอังกฤษและการงดออกเสียงทุกตำแหน่ง

## เตรียมการเลือกตั้งจริง

1. ยืนยันกติกาของ Chapter: ผู้มีสิทธิ์ ผู้สมัครแต่ละตำแหน่ง วาระ การเลือกตั้งที่มีผู้สมัครคนเดียว วิธีตัดสินคะแนนเสมอ และเกณฑ์รับรองผล ระบบนี้นับคะแนนแต่ไม่ประกาศผู้ชนะอัตโนมัติ
2. เติมชื่อ ประวัติ และสังกัดผู้สมัครที่ยินยอมเผยแพร่ใน `config.json` โดยใช้ ID ที่ไม่ซ้ำในแต่ละตำแหน่ง เพิ่มตำแหน่งใน `offices` ได้
3. ตั้ง `opensAt` และ `closesAt` เป็น ISO 8601 พร้อมเขตเวลา เช่น `2027-01-15T09:00:00+07:00` (ตัวอย่างรูปแบบเท่านั้น) วันเวลาบนเครื่องเซิร์ฟเวอร์ต้องถูกต้อง
4. ติดตั้ง API ใน `backend/server.py` บนเครื่องที่เปิดตลอดเวลาพร้อม HTTPS reverse proxy และกำหนด `apiBase` เป็น URL ของบริการนั้น GitHub Pages รัน API หรือฐานข้อมูลไม่ได้
5. สร้างฐานข้อมูลจาก configuration ที่ยืนยันแล้ว ออกรหัสลับให้ผู้มีสิทธิ์คนละหนึ่งรหัสก่อนเปิดลงคะแนน และส่งให้แต่ละคนเป็นการส่วนตัว การใช้รหัสยืนยันสิทธิ์อาศัยผู้จัดตรวจรายชื่อ ไม่ใช่การเข้าสู่ระบบมหาวิทยาลัย
6. ตั้ง `mode` เป็น `live` หลังทดสอบการเชื่อมต่อแล้ว ในโหมดนี้ข้อมูลตำแหน่งและผู้สมัครจะอ่านจาก API ซึ่งยึด configuration ตอนสร้างฐานข้อมูล หากต้องแก้ก่อนเปิด ให้จัดทำการเลือกตั้งใหม่และแจ้งยกเลิกรหัสเดิม

## ส่วนรับคะแนน

ใช้ Python 3.10 ขึ้นไปและ SQLite ใน standard library ส่วนตรวจและแปลงรูปผู้สมัครใช้ Pillow ตาม backend/requirements.txt
ตัวอย่างบนเครื่องของผู้ดูแล (ใช้ interpreter แบบ absolute path):

```sh
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" init --config config.json
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" issue --roster "$HOME/ecs-private/eligible.csv" --output "$HOME/ecs-private/codes.csv"
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" serve --origin https://ecs-thai.github.io --port 8766
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" results
```

คำสั่งทำจากโฟลเดอร์ `student-election` และไฟล์รายชื่อมีหัวคอลัมน์ `email` ให้เก็บ `ecs-private` อยู่นอกโฟลเดอร์เว็บและ git เสมอ สำรองฐานข้อมูลในพื้นที่ส่วนตัว ใช้บริการระบบดูแล process และ reverse proxy จำกัดขนาดและอัตราคำขอ บริการ Python ผูกกับ localhost เท่านั้น

API: `GET /election` คืนข้อมูลสาธารณะ, `POST /ballots` รับ `{electionId, email, token, choices}` ผลรวมเรียกได้จากคำสั่ง results หลังปิดเท่านั้น ไม่มี HTTP endpoint ดูรายชื่อหรือผลรวม

รหัสถูกเก็บเป็น hash และใช้ได้ครั้งเดียว การบันทึกสถานะรหัสและบัตรทำใน transaction เดียว การส่งซ้ำคืนรหัสยืนยันเดิมและไม่เพิ่มคะแนน ไม่เก็บชื่อ อีเมล รหัสผู้ลงคะแนน หรือเวลาในตารางบัตร รหัสยืนยันไม่ได้เชื่อมกับบัตร อย่างไรก็ดีระบบนี้ต้องไว้วางใจผู้ดูแลเซิร์ฟเวอร์/ฐานข้อมูล ไม่ใช่การลงคะแนนแบบเข้ารหัสที่ตรวจสอบความลับจากผู้ดูแลได้ หลีกเลี่ยง logging เนื้อหาคำขอที่ proxy และอย่าเผยแพร่ฐานข้อมูลหรือรหัสใน GitHub

ยังไม่ได้ติดตั้ง API สาธารณะหรือเปิดเลือกตั้งจริง และไม่ส่งข้อความ/รหัสใด ๆ ให้นักศึกษาโดยอัตโนมัติ

## ตรวจสอบ

```sh
"$HOME/.venvs/research/bin/python" -m unittest discover -s backend -v
```

ทดสอบส่งซ้ำพร้อมกัน บัตรไม่ถูกต้อง รหัสผิด ช่วงเวลาเลือกตั้ง การออกรหัสซ้ำ และผลรวมหลังปิด

## รหัส 3 ตัวและรายชื่อนิสิต

ระบบรุ่นนี้ใช้ **อีเมล + รหัส 3 ตัว** (A–Z และ 2–9 โดยตัด I/O ออก) เช่น K7P รหัสผูกกับอีเมล ไม่ได้ใช้รหัสสั้นเพียงอย่างเดียว ตัวพิมพ์เล็ก/ใหญ่ใช้ได้เหมือนกัน รหัสไม่จำเป็นต้องไม่ซ้ำกันข้ามอีเมล เพราะตรวจทั้งสองอย่างคู่กัน ลงคะแนนสำเร็จได้ครั้งเดียว และส่งซ้ำด้วยข้อมูลเดิมคืนใบยืนยันเดิม เมื่อผิด 5 ครั้งจะระงับจนผู้ดูแลปลดล็อก ไม่มีการปลดล็อกอัตโนมัติ

ไฟล์ตัวอย่างหัวคอลัมน์อยู่ใน `templates/eligible-students.csv` (`name,email`) และ `templates/candidates.csv` (`name,email`) สำเนาที่กรอกข้อมูลจริงต้องเก็บนอก repository เท่านั้น office ใช้ `president`, `vice_president`, `secretary`, `treasurer`

คำสั่ง `issue` สร้างไฟล์ส่วนตัวที่มีชื่อ อีเมล และรหัส 3 ตัว คำสั่งด้านล่างสร้างอีเมลร่างแยกคน (.eml) **ยังไม่ส่งอีเมล** ต้องกำหนดผู้ส่งจริงและตรวจรายชื่อก่อนส่งผ่านระบบอีเมลที่จะเลือกใช้:

```sh
"$HOME/.venvs/research/bin/python" backend/prepare_mail.py --input "$HOME/ecs-private/codes.csv" --output "$HOME/ecs-private/voter-mail" --sender organizer@example.org --kind voters
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" unlock --email student@example.org
```

การปลดล็อกไม่ล้างสถานะลงคะแนนแล้ว และไม่อนุญาตให้ลงคะแนนซ้ำ อีเมลและรหัสจะไม่เก็บในตารางบัตร ฐานข้อมูลเก็บ hash อีเมลและ keyed hash รหัส เก็บฐานข้อมูลและไฟล์รหัสให้เป็นความลับ Backend จำกัด 30 คำขอต่อนาทีต่อ IP ที่เชื่อมต่อโดยตรง หากใช้ reverse proxy คำขออาจใช้โควตาร่วมกัน ต้องตั้ง rate limit ที่ proxy ให้เหมาะกับจำนวนผู้ใช้และไม่บันทึกเนื้อหาคำขอ

## การส่งรูปและประวัติผู้สมัคร

หน้า `candidate.html` มีตัวอย่างฟอร์มที่ไม่ส่งข้อมูล เมื่อเชื่อม API แล้ว ผู้สมัครจะใช้ลิงก์เชิญส่วนตัวที่มี token ยาว (ต่างจากรหัสลงคะแนน 3 ตัว) ลิงก์หมดอายุเริ่มต้น 14 วัน ผู้สมัครเลือกตำแหน่งเองจาก 4 ตำแหน่ง และแก้ไขได้ก่อนปิดรับข้อมูล การเปลี่ยนตำแหน่งจะกลับสู่สถานะรอตรวจรับ

1. ติดตั้ง Pillow ด้วย `uv pip install --python "$HOME/.venvs/research/bin/python" -r backend/requirements.txt`
2. เริ่มฐานข้อมูลด้วย `config.json` โหมด draft ได้ ยังไม่ต้องมีผู้สมัครหรือวันเลือกตั้ง ตั้ง `apiBase` ใน config หน้าเว็บเมื่อติดตั้ง API พร้อม HTTPS แล้ว โดยคง mode เป็น draft ระหว่างรับประวัติ
3. สร้างลิงก์ส่วนตัวและอีเมลร่างจากรายชื่อผู้สมัคร:

```sh
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-private/election.sqlite" invite --roster "$HOME/ecs-private/candidates.csv" --output "$HOME/ecs-private/candidate-links.csv"
"$HOME/.venvs/research/bin/python" backend/prepare_mail.py --input "$HOME/ecs-private/candidate-links.csv" --output "$HOME/ecs-private/candidate-mail" --sender organizer@example.org --kind candidates
```

4. ผู้สมัครเลือกตำแหน่ง กรอกชื่อ สังกัด ประวัติไม่เกิน 3,000 ตัวอักษร และอัปโหลด JPG/PNG สูงสุด 5 MB / 20 ล้านพิกเซล ระบบตรวจไฟล์จริง ย่อรูปไม่เกิน 1,000×1,000 และเขียนเป็น JPEG ใหม่โดยไม่คง EXIF ต้องยินยอมเผยแพร่ก่อนส่ง ข้อมูลที่ส่งเข้ามายังเป็นส่วนตัว
5. ผู้ดูแลส่งออกข้อมูลไปพื้นที่ส่วนตัวเพื่อตรวจ แล้วอนุมัติเป็นรายคน:

```sh
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-private/election.sqlite" export --output "$HOME/ecs-private/review-1"
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-private/election.sqlite" approve --id CANDIDATE_ID
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-private/election.sqlite" export --approved-only --output "$HOME/ecs-private/approved-1"
```

ผู้สมัครแก้ไขผ่านลิงก์เดิมได้ก่อนหมดอายุ/ก่อนเปิดลงคะแนน ทุกการแก้ไขกลับสู่สถานะรอตรวจรับ ต้องอนุมัติอีกครั้งก่อนใช้ฉบับใหม่

6. เมื่อผู้สมัครและเวลาได้รับการยืนยันแล้ว ใช้ `schedule` สร้าง snapshot รายชื่อที่อนุมัติลงในฐานข้อมูลและไฟล์ configuration สาธารณะ นำเฉพาะรูปที่อนุมัติไปยัง `photos/` และนำ public config ไปแทน config หน้าเว็บ คำสั่งจะไม่ยอมแก้การเลือกตั้งที่เปิดแล้ว:

```sh
"$HOME/.venvs/research/bin/python" backend/candidates.py --db "$HOME/ecs-private/election.sqlite" schedule --opens 2027-01-15T09:00:00+07:00 --closes 2027-01-16T17:00:00+07:00 --api https://YOUR-API-HOST --output "$HOME/ecs-private/public-config.json" --photos photos
```

วันข้างต้นเป็นตัวอย่าง ไม่ใช่กำหนดการจริง หากมีการแก้ประวัติหลัง schedule ให้ตรวจรับและ schedule/export ใหม่ก่อนเปิดเพื่อเผยแพร่ฉบับล่าสุด ตารางบัตรใช้ snapshot เดียวตลอดการเลือกตั้ง

หมายเหตุการอัปเกรด: schema รหัส 3 ตัวต่างจากรุ่น token ยาวเดิม ปัจจุบันยังไม่มีฐานข้อมูลเลือกตั้งจริง ให้ init ฐานข้อมูลใหม่ ห้ามนำไฟล์ฐานข้อมูลเก่ามาทับหรือย้ายคะแนนโดยไม่ตรวจสอบ
