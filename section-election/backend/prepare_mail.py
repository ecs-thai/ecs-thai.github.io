"""Create private per-recipient .eml drafts. This command never sends email."""
import argparse,csv,os
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path

def prepare(source,output,sender,kind):
    with open(source,encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    out=Path(output);out.mkdir(parents=True,exist_ok=False);os.chmod(out,0o700)
    for i,row in enumerate(rows,1):
        msg=EmailMessage(policy=SMTP);msg['From']=sender;msg['To']=row['email']
        name=row.get('name','')
        if kind=='voters':
            msg['Subject']='รหัสลงคะแนน | ECS Thailand Section'
            body=f'''เรียน {name}\n\nรหัสลงคะแนนของคุณ: {row['voting_code']}\nใช้คู่กับอีเมล: {row['email']}\nเปิดบัตรเลือกตั้ง: https://ecs-thai.github.io/section-election/\n\nลงคะแนนได้หนึ่งครั้ง กรุณาเก็บรหัสเป็นความลับ หากลองรหัสผิดครบ 5 ครั้งให้ติดต่อผู้จัด\nวันเปิด–ปิดและรายชื่อผู้สมัครจะแสดงในระบบเมื่อยืนยันแล้ว\n\nYour voting code is {row['voting_code']}. Use it with this email address. You may submit one ballot. Keep the code private. Contact the organizer if access is locked after five failed attempts.'''
        else:
            msg['Subject']='ส่งรูปและประวัติผู้สมัคร | ECS Thailand Section'
            body=f'''เรียน {name}\n\nกรุณาเลือกตำแหน่งที่ต้องการสมัคร พร้อมส่งรูปและประวัติ ผ่านลิงก์ส่วนตัวนี้:\n{row['upload_link']}\n\nใช้รูป JPG/PNG ไม่เกิน 5 MB และประวัติไม่เกิน 3,000 ตัวอักษร ข้อมูลจะรอผู้จัดตรวจรับก่อนเผยแพร่ โปรดอย่าส่งต่อลิงก์นี้\n\nPlease use your personal link to choose your position and submit a JPG/PNG photo (up to 5 MB) and biography (up to 3,000 characters). The organizer will review your profile before publication. Keep the link private.'''
        msg.set_content(body);file=out/f'{i:04d}.eml';file.write_bytes(msg.as_bytes());os.chmod(file,0o600)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--sender',required=True);p.add_argument('--kind',choices=['voters','candidates'],required=True);a=p.parse_args();prepare(a.input,a.output,a.sender,a.kind)
