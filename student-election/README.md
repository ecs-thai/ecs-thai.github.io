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

ใช้ Python 3.10 ขึ้นไปและ SQLite ใน standard library ไม่ต้องติดตั้งแพ็กเกจ
ตัวอย่างบนเครื่องของผู้ดูแล (ใช้ interpreter แบบ absolute path):

```sh
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" init --config config.json
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" issue --roster "$HOME/ecs-private/eligible.csv" --output "$HOME/ecs-private/codes.csv"
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" serve --origin https://ecs-thai.github.io --port 8766
"$HOME/.venvs/research/bin/python" backend/server.py --db "$HOME/ecs-private/election.sqlite" results
```

คำสั่งทำจากโฟลเดอร์ `student-election` และไฟล์รายชื่อมีหัวคอลัมน์ `email` ให้เก็บ `ecs-private` อยู่นอกโฟลเดอร์เว็บและ git เสมอ สำรองฐานข้อมูลในพื้นที่ส่วนตัว ใช้บริการระบบดูแล process และ reverse proxy จำกัดขนาดและอัตราคำขอ บริการ Python ผูกกับ localhost เท่านั้น

API: `GET /election` คืนข้อมูลสาธารณะ, `POST /ballots` รับ `{electionId, token, choices}` ผลรวมเรียกได้จากคำสั่ง results หลังปิดเท่านั้น ไม่มี HTTP endpoint ดูรายชื่อหรือผลรวม

รหัสถูกเก็บเป็น hash และใช้ได้ครั้งเดียว การบันทึกสถานะรหัสและบัตรทำใน transaction เดียว การส่งซ้ำคืนรหัสยืนยันเดิมและไม่เพิ่มคะแนน ไม่เก็บชื่อ อีเมล รหัสผู้ลงคะแนน หรือเวลาในตารางบัตร รหัสยืนยันไม่ได้เชื่อมกับบัตร อย่างไรก็ดีระบบนี้ต้องไว้วางใจผู้ดูแลเซิร์ฟเวอร์/ฐานข้อมูล ไม่ใช่การลงคะแนนแบบเข้ารหัสที่ตรวจสอบความลับจากผู้ดูแลได้ หลีกเลี่ยง logging เนื้อหาคำขอที่ proxy และอย่าเผยแพร่ฐานข้อมูลหรือรหัสใน GitHub

ยังไม่ได้ติดตั้ง API สาธารณะหรือเปิดเลือกตั้งจริง และไม่ส่งข้อความ/รหัสใด ๆ ให้นักศึกษาโดยอัตโนมัติ

## ตรวจสอบ

```sh
"$HOME/.venvs/research/bin/python" -m unittest discover -s backend -v
```

ทดสอบส่งซ้ำพร้อมกัน บัตรไม่ถูกต้อง รหัสผิด ช่วงเวลาเลือกตั้ง การออกรหัสซ้ำ และผลรวมหลังปิด
