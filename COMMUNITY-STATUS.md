# ECS Community: สถานะและวิธีทำงานต่อ

ปรับปรุง 22 กันยายน 2026

## ทำแล้ว

- พื้นที่ชุมชน: https://ecs-thai.github.io/community/
- เพิ่มเมนูชุมชนและทางเข้าจากหน้าแรกของเว็บเดิม
- บอร์ดโอกาสวิจัย: intern, ผู้ช่วยวิจัย, ป.โท, ป.เอก, postdoc และงาน
- ทำเนียบแล็บ: สถาบัน สถานที่ หัวข้อวิจัย เทคนิค รายละเอียดและช่องทางติดต่อ
- กิจกรรม: วันเวลาแบบเวลาไทย ลิงก์ลงทะเบียน และไฟล์ปฏิทิน ICS
- ค้นหา กรองประเภท และดูคลังประกาศที่ปิดหรือหมดอายุ
- สมาชิกขอสิทธิ์ลงประกาศ ผู้ดูแลตรวจสอบและสร้างลิงก์ส่วนตัวอายุ 30 วัน
- เจ้าของสร้าง แก้ไข ปิด หรือถอนประกาศได้ การแก้ไขกลับไปรอตรวจรับ
- หน้าผู้ดูแลตรวจรับ ส่งกลับแก้ไข ซ่อนประกาศ ดูรายงานปัญหาและระงับลิงก์สมาชิก
- Cloudflare Worker และ D1 แยกจากระบบเลือกตั้งทั้งหมด
- ทดสอบบน staging แยก: ทั้งสามหมวด สิทธิ์เจ้าของ การตรวจรับ การแก้ไขแล้วซ่อนก่อนตรวจใหม่ การป้องกันอนุมัติรุ่นเก่า การปิดประกาศ รายงานปัญหา ลิงก์ไม่ปลอดภัย และระงับสมาชิก ผ่าน
- ไม่ใส่ประกาศหรือข้อมูลสมาชิกสมมติในระบบจริง

## วิธีใช้งานสำหรับผู้ดูแล

1. เปิด community/admin.html จากเว็บ กรอกรหัสผู้ดูแลที่เก็บไว้ในเครื่องที่ ~/ecs-community-private/admin-token ห้ามนำค่ารหัสลง Git หรือแชต
2. สมาชิกกด “ร่วมลงประกาศ” ส่งชื่อและอีเมล ผู้ดูแลตรวจสอบตัวตนและสิทธิ์ในการลงประกาศ
3. กดสร้างลิงก์ส่วนตัว คัดลอกส่งให้สมาชิกทางอีเมลด้วยตนเอง ลิงก์หมดอายุ 30 วัน การสร้างใหม่ยกเลิกลิงก์เดิม
4. สมาชิกเปิดลิงก์ กรอกประกาศและยินยอมเผยแพร่อีเมลติดต่อ ผู้ดูแลอ่านรายละเอียดก่อนอนุมัติ
5. เมื่อรับครบ สมาชิกปิดประกาศได้ หากมีปัญหาผู้ดูแลซ่อนประกาศและจัดการรายงาน

การมีลิงก์ลงประกาศไม่ได้ยืนยันสถานะสมาชิก ECS โดยอัตโนมัติ ผู้ดูแลต้องตรวจสอบก่อนให้สิทธิ์ ไม่มีการส่งอีเมลหรือสร้างบัญชีสมาชิกจริงโดยอัตโนมัติในรอบติดตั้งนี้

## ยังเหลือ / รอข้อมูล

- รออีเมลผู้ส่งและบริการส่งอีเมลที่ยืนยันแล้ว เพื่อเปิดการส่งลิงก์เข้าใช้งานและเตือนก่อนหมดอายุแบบอัตโนมัติ ปัจจุบันส่งลิงก์ด้วยตนเอง
- เติมประกาศ แล็บและกิจกรรมจริง พร้อมกำหนดผู้ดูแลรับผิดชอบ
- ฟีเจอร์ระยะต่อไปยังไม่ได้ทำ: บอร์ดหาความร่วมมือแยกหมวด ข่าวผลงานสมาชิก จดหมายข่าวตามความสนใจ คลังความรู้ และความคิดเห็นใต้โพสต์
- ยังไม่มีระบบรับใบสมัคร/CV ภายในเว็บ ให้ใช้ลิงก์สมัครหรืออีเมลของเจ้าของประกาศ
- กำหนดรอบสำรองข้อมูลและระยะเวลาเก็บคำขอ/รายงานปัญหา ตรวจโควตาการใช้งานเป็นระยะ

## Technical handoff

Production Worker: ecs-community. D1: 321c31e9-e270-45de-8279-88eb14c59ab3. Configuration: community/cloudflare/wrangler.jsonc.

Staging Worker: ecs-community-staging. Separate D1 and private administrator credential. Run community/cloudflare/test-staging.py using the absolute research Python interpreter; this targets staging only and sends no email. Repeated rapid tests may hit the 40 requests/minute limit.

Deploy from community/cloudflare using Wrangler. ADMIN_TOKEN is a Worker secret; production copy lives outside Git at ~/ecs-community-private/admin-token. All post writes require a valid owner link. Moderation requires the administrator secret. Public rendering uses text nodes, not submitted HTML. Public links are restricted to HTTP(S). No third-party trackers are added. Member links are bearer credentials: keep private, rotate by creating a replacement, and revoke if exposed.

Back up D1 with wrangler d1 export ecs-community --remote --output PRIVATE_FILE, outside Git. Public listing currently returns up to 500 posts; add pagination before exceeding that volume. No R2 or paid mail service is required by this release.
