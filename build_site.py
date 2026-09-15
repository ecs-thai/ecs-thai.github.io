#!/usr/bin/env python3
"""Build the bilingual ECS Thailand public website using Python's standard library."""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'content.json').read_text())
SECTION = DATA['section']
MEETINGS = sorted(DATA['meetings'], key=lambda m: m['date'], reverse=True)
NEWS = sorted(DATA['news'], key=lambda n: n['date'], reverse=True)
ANNOUNCEMENT = 'https://www.electrochem.org/ecsnews/ecs-thailand-section'
BYLAWS = 'https://www.electrochem.org/wp-content/uploads/2024/07/2024-05-30-ECS-Thailand-Section-Bylaws.pdf'


def esc(value):
    return html.escape(str(value), quote=True)


def pair(th, en, tag='span'):
    return f'<{tag} lang="th" data-lang="th">{esc(th)}</{tag}><{tag} lang="en" data-lang="en" hidden>{esc(en)}</{tag}>'


def tr(value, tag='span'):
    return pair(value['th'], value['en'], tag)


def safe_url(value):
    parts = urlsplit(value)
    if parts.scheme not in ('', 'https', 'mailto') or value.startswith('//'):
        raise ValueError(f'Unsupported URL: {value}')
    if not parts.scheme and ('..' in parts.path.split('/') or parts.path.startswith('/')):
        raise ValueError(f'Use a local filename for internal links: {value}')
    return esc(value)


def link(url, th, en, cls='text-link'):
    return f'<a class="{cls}" href="{safe_url(url)}">{pair(th,en)}</a>'


def date_text(value):
    d = date.fromisoformat(value)
    months_th = ['มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']
    months_en = ['January','February','March','April','May','June','July','August','September','October','November','December']
    return pair(f'{d.day} {months_th[d.month-1]} {d.year}', f'{d.day} {months_en[d.month-1]} {d.year}')


def validate():
    ids = set()
    for m in MEETINGS:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:-[a-z0-9-]+)?', m['id']):
            raise ValueError('Meeting IDs must start with YYYY-MM-DD.')
        if m['id'] in ids: raise ValueError('Duplicate meeting ID')
        ids.add(m['id']); date.fromisoformat(m['date'])
        for item in m['materials']: safe_url(item['url'])
        if m.get('minutes'):
            if m['minutes'].get('status') not in ('draft','approved'): raise ValueError('Minutes require draft or approved status.')
            safe_url(m['minutes']['url'])
    for n in NEWS:
        date.fromisoformat(n['date']); safe_url(n['url'])


NAV = [('index.html','home','หน้าแรก','Home'),('about.html','about','เกี่ยวกับเรา','About'),('activities.html','activities','ข่าวและกิจกรรม','News & activities'),('meetings.html','meetings','การประชุม','Meetings'),('join.html','join','เข้าร่วม ECS','Join ECS')]


def header(current):
    nav=''.join(f'<a href="{url}"'+(' aria-current="page"' if current==key else '')+f'>{pair(th,en)}</a>' for url,key,th,en in NAV)
    return f'''<a class="skip-link" href="#main">{pair('ข้ามไปเนื้อหา','Skip to content')}</a>
<header class="site-header"><div class="wrap header-inner"><a class="brand" href="index.html"><strong>ECS Thailand Section</strong><small>The Electrochemical Society</small></a>
<nav class="site-nav" id="site-nav" aria-label="เมนูหลัก" data-label-th="เมนูหลัก" data-label-en="Main navigation">{nav}</nav>
<div class="language-switch" role="group" aria-label="Language / ภาษา"><button type="button" data-language="th" aria-pressed="true" aria-label="ภาษาไทย">TH</button><button type="button" data-language="en" aria-pressed="false" aria-label="English">EN</button></div>
<button class="menu-toggle" type="button" aria-controls="site-nav" aria-expanded="false">{pair('เมนู','Menu')} ☰</button></div></header>'''


def footer():
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-top"><div><strong>ECS Thailand Section</strong><p>{pair('เครือข่ายเคมีไฟฟ้าและวิทยาศาสตร์สถานะของแข็งในประเทศไทย','A community for electrochemical and solid-state science in Thailand.')}</p></div><div class="footer-links">{link('https://www.electrochem.org/','เว็บไซต์ ECS','ECS website')}{link('https://www.electrochem.org/sections','ECS Sections','ECS Sections')}{link(BYLAWS,'ข้อบังคับ Section','Section bylaws')}{link('join.html','การเป็นสมาชิก','Membership')}</div></div><div class="footer-bottom"><span>© 2026 ECS Thailand Section</span><span>{pair('ข่าวกิจกรรม · เอกสารประชุม · รายงานการประชุม','Activities · Meeting resources · Minutes')}</span></div></div></footer>'''


def page(filename, current, title_th, title_en, body):
    desc='ECS Thailand Section — community, activities, meeting resources and minutes. เครือข่าย ECS ประเทศไทย กิจกรรมและเอกสารประชุม'
    result=f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="referrer" content="no-referrer"><meta name="description" content="{esc(desc)}"><meta name="color-scheme" content="light"><title>{esc(title_th)} | ECS Thailand Section</title><link rel="stylesheet" href="site.css"><script src="site.js" defer></script></head><body data-title-th="{esc(title_th)} | ECS Thailand Section" data-title-en="{esc(title_en)} | ECS Thailand Section">{header(current)}<noscript><div class="no-script">เว็บไซต์แสดงภาษาไทยเมื่อปิด JavaScript · Enable JavaScript to switch to English.</div></noscript><main id="main">{body}</main>{footer()}</body></html>'''
    (ROOT/filename).write_text(result)


def intro(th, en, description, eyebrow=('ECS THAILAND SECTION','ECS THAILAND SECTION'), extra=''):
    return f'<section class="page-intro"><div class="wrap"><p class="eyebrow">{pair(*eyebrow)}</p><h1>{pair(th,en)}</h1><p class="lead">{tr(description)}</p>{extra}</div></section>'


def pillars():
    items=[('แลกเปลี่ยนความรู้','Exchange knowledge','เชื่อมโยงงานวิจัยพื้นฐานกับการประยุกต์ใช้ ผ่านการสนทนาทางวิชาการ','Connect fundamental research and practical applications through scientific exchange.'),('สนับสนุนนักวิจัยรุ่นใหม่','Support emerging researchers','ส่งเสริมการเรียนรู้และการมีส่วนร่วมของนักวิจัยในช่วงเริ่มต้นเส้นทางอาชีพ','Encourage learning and participation among researchers at the beginning of their careers.'),('สร้างเครือข่ายวิชาการ','Build professional connections','เชื่อมโยงนักวิทยาศาสตร์ วิศวกร และสมาชิกที่สนใจเคมีไฟฟ้าและวัสดุ','Connect scientists, engineers and members interested in electrochemistry and materials.')]
    return '<div class="pillars">'+''.join(f'<div class="pillar"><span class="num">0{i+1}</span><h3>{pair(th,en)}</h3><p>{pair(dt,de)}</p></div>' for i,(th,en,dt,de) in enumerate(items))+'</div>'


def news_rows(items):
    return ''.join(f'<a class="news-row" href="{safe_url(n["url"])}"><div class="date-block"><time datetime="{esc(n["date"])}">{date_text(n["date"])}</time></div><div><span class="badge">{tr(n["category"])}</span><h3>{tr(n["title"])}</h3><p>{tr(n["summary"])}</p></div><span class="arrow" aria-hidden="true">↗</span></a>' for n in items)


def meeting_url(m): return f'meeting-{m["id"]}.html'


def home():
    latest=MEETINGS[0] if MEETINGS else None
    visual='''<div class="science-panel"><div class="panel-top">ELECTROCHEMISTRY · SOLID-STATE SCIENCE</div><svg viewBox="0 0 330 235" fill="none" aria-hidden="true"><g stroke="#90c9c3" stroke-width="1.1"><ellipse cx="165" cy="114" rx="135" ry="54"/><ellipse cx="165" cy="114" rx="135" ry="54" transform="rotate(60 165 114)"/><ellipse cx="165" cy="114" rx="135" ry="54" transform="rotate(120 165 114)"/></g><circle cx="165" cy="114" r="21" fill="#b4e0d0"/><circle cx="43" cy="90" r="6" fill="#dfba69"/><circle cx="211" cy="14" r="6" fill="#b4e0d0"/><circle cx="246" cy="178" r="6" fill="#b4e0d0"/><path d="M24 222H306" stroke="#4b6c7d"/></svg><div class="panel-bottom"><strong>Thailand</strong>'''+pair('เชื่อมโยงกับชุมชนวิทยาศาสตร์ทั่วโลก','Connected to a global scientific community')+'</div></div>'
    body=f'''<section class="hero"><div class="wrap hero-grid"><div><p class="eyebrow">THE ELECTROCHEMICAL SOCIETY · THAILAND</p><h1>{pair('เชื่อมโยงชุมชนเคมีไฟฟ้าในประเทศไทย','Connecting Thailand’s electrochemistry community')}</h1><p class="lead">{pair('ร่วมแลกเปลี่ยนความรู้ด้านเคมีไฟฟ้าและวิทยาศาสตร์สถานะของแข็ง สนับสนุนนักวิจัยรุ่นใหม่ และสร้างความร่วมมือระหว่างนักวิทยาศาสตร์กับวิศวกร','Sharing electrochemical and solid-state science, supporting early-career researchers, and connecting scientists and engineers.')}</p><div class="actions">{link('about.html','รู้จัก ECS Thailand Section','Discover the Section','button')}{link('meetings.html','เอกสารการประชุม →','Meeting resources →')}</div></div>{visual}</div></section>'''
    if latest:
        body+=f'''<section class="section white"><div class="wrap"><div class="section-header"><div><p class="eyebrow">{pair('ข้อมูลการประชุม','MEETING RESOURCES')}</p><h2>{pair('รวมทุกอย่างสำหรับการประชุม','Everything for your meeting')}</h2></div>{link('meetings.html','คลังการประชุมทั้งหมด →','Browse all meetings →')}</div><div class="feature-grid"><article class="meeting-feature"><span class="badge">{tr(latest['format'])}</span><h3>{tr(latest['title'])}</h3><div class="meta"><p>{date_text(latest['date'])} · {tr(latest['time'])}</p><p>{tr(latest['venue'])}</p></div><p class="summary">{tr(latest['summary'])}</p>{link(meeting_url(latest),'เปิดหน้าการประชุม','Open meeting resources','button')}</article><div class="resource-teaser"><h3>{pair('เอกสารและเครื่องมือ','Documents & tools')}</h3>'''
        for r in latest['materials'][:2]+latest['materials'][3:4]:
            body+=f'<a class="teaser-row" href="{safe_url(r["url"])}"><strong>{tr(r["title"])}<span aria-hidden="true">↗</span></strong><p>{tr(r["detail"])}</p></a>'
        body+='</div></div></div></section>'
    body+=f'<section class="section"><div class="wrap"><div class="section-header"><div><p class="eyebrow">{pair("สิ่งที่เรามุ่งส่งเสริม","OUR PURPOSE")}</p><h2>{pair("ความรู้ ผู้คน และโอกาสในการร่วมงาน","Knowledge, people and collaboration")}</h2></div></div>{pillars()}</div></section>'
    body+=f'<section class="section white"><div class="wrap"><div class="section-header"><div><p class="eyebrow">{pair("ข่าวประชาสัมพันธ์","SECTION UPDATES")}</p><h2>{pair("ข่าวและกิจกรรม","News & activities")}</h2></div>{link("activities.html","ดูข่าวทั้งหมด →","All updates →")}</div>{news_rows(NEWS[:3])}</div></section>'
    body+=f'<section class="join-band"><div class="wrap join-grid"><div><h2>{pair("ร่วมเป็นส่วนหนึ่งของเครือข่าย ECS","Be part of the ECS community")}</h2><p>{pair("ศึกษาการเป็นสมาชิก ECS และวิธีเข้าร่วม Thailand Section","Explore ECS membership and learn how to affiliate with Thailand Section.")}</p></div>{link("join.html","วิธีเข้าร่วม ECS","How to join","button")}</div></section>'
    page('index.html','home','หน้าแรก','Home',body)


def about():
    body=intro('เกี่ยวกับ ECS Thailand Section','About ECS Thailand Section',{'th':'เครือข่ายของ The Electrochemical Society ในประเทศไทย เพื่อการแลกเปลี่ยนความรู้และความร่วมมือทางวิชาการ','en':'The Thailand-based community of The Electrochemical Society, advancing scientific exchange and professional connections.'})
    body+=f'''<section class="section white"><div class="wrap"><div class="prose"><h2>{pair('เครือข่ายของเรา','Our community')}</h2><p>{pair('ECS Thailand Section ได้รับการรับรองการจัดตั้งจากคณะกรรมการบริหาร ECS เมื่อวันที่ 30 พฤษภาคม 2024 เรามุ่งส่งเสริมเคมีไฟฟ้าและวิทยาศาสตร์สถานะของแข็ง เชื่อมโยงการวิจัยพื้นฐานกับการประยุกต์ใช้ และสนับสนุนการมีส่วนร่วมของนักวิจัยรุ่นใหม่','ECS Thailand Section was chartered by the ECS Board of Directors on 30 May 2024. We promote electrochemical and solid-state science, connect fundamental and applied research, and support participation by early-career researchers.')}</p><p class="source-line">{pair('อ้างอิง: ','Sources: ')}{link(ANNOUNCEMENT,'ประกาศจัดตั้งจาก ECS','ECS charter announcement') } · {link(BYLAWS,'ข้อบังคับ Thailand Section ข้อ I–II','Thailand Section Bylaws, Articles I–II')}</p></div>{pillars()}<div class="prose"><h2>{pair('ประธาน Section','Section Chair')}</h2><div class="leadership"><div class="role">Chair</div><div><h3>{esc(SECTION['chair'])}</h3><p>{pair('ประธาน ECS Thailand Section','Chair, ECS Thailand Section')}</p></div></div><h2>{pair('คณะกรรมการและการกำกับดูแล','Committee & governance')}</h2><p>{pair('ตามข้อบังคับ Section มีตำแหน่ง Chair, Vice Chair, Secretary และ Treasurer รวมถึงกรรมการ Members-at-Large อย่างน้อยสองคน รายละเอียดโครงสร้างคณะกรรมการและกระบวนการเลือกตั้งอยู่ในข้อบังคับของ Section','The Section bylaws define the offices of Chair, Vice Chair, Secretary and Treasurer, together with at least two Members-at-Large. The bylaws set out the full Executive Committee structure and election process.')}</p><div class="actions">{link(BYLAWS,'อ่านข้อบังคับ Section','Read the Section bylaws','button secondary')}{link('https://www.electrochem.org/section-officers','รายชื่อกรรมการบนเว็บไซต์ ECS ↗','ECS officer directory ↗')}</div><h2>{pair('เว็บไซต์นี้รวบรวมอะไรบ้าง','What this website contains')}</h2><p>{pair('ข้อมูลแนะนำ Section ข่าวประชาสัมพันธ์กิจกรรม และคลังการประชุมที่เชื่อมเอกสารเตรียมประชุมกับรายงานการประชุมของแต่ละครั้ง เพื่อให้สมาชิกติดตามงานและค้นข้อมูลย้อนหลังได้','Section information, activity announcements and a meeting archive that brings together preparation materials and published minutes for each meeting.')}</p></div></div></section>'''
    page('about.html','about','เกี่ยวกับเรา','About',body)


def activities():
    body=intro('ข่าวและกิจกรรม','News & activities',{'th':'ประกาศการประชุม กิจกรรมทางวิชาการ และข่าวสารของ ECS Thailand Section','en':'Meeting announcements, scientific activities and news from ECS Thailand Section.'})
    body+=f'<section class="section white"><div class="wrap">{news_rows(NEWS)}<div class="activity-note"><p>{pair("ประกาศกิจกรรมใหม่จะเพิ่มในหมวดนี้ พร้อมรายละเอียด วันเวลา และช่องทางเข้าร่วม ส่วนแนวคิดกิจกรรมที่ยังอยู่ระหว่างหารือจะอยู่ในเอกสารการประชุมของแต่ละครั้ง","New activity announcements will include details, dates and participation information. Ideas still under discussion remain in the relevant meeting materials.")}</p>{link("meetings.html","ดูเอกสารและแผนที่นำเข้าประชุม →","Explore meeting discussions and plans →")}</div></div></section>'
    page('activities.html','activities','ข่าวและกิจกรรม','News & activities',body)


def archive():
    body=intro('คลังการประชุม','Meeting archive',{'th':'เลือกการประชุมเพื่อเปิดวาระ สไลด์ เอกสารประกอบ และรายงานการประชุมที่เผยแพร่แล้ว','en':'Find agendas, slides, briefing documents and published minutes for each meeting.'})
    body+=f'''<section class="section white"><div class="wrap"><div class="archive-tools"><div class="field"><label for="archive-search">{pair('ค้นหาการประชุม','Find a meeting')}</label><input id="archive-search" type="search" placeholder="ชื่อการประชุมหรือวันที่" data-placeholder-th="ชื่อการประชุมหรือวันที่" data-placeholder-en="Meeting title or date"></div><div class="field narrow"><label for="archive-type">{pair('ประเภทเอกสาร','Documents')}</label><select id="archive-type"><option value="all">ทั้งหมด / All meetings</option><option value="minutes">มีรายงานการประชุม / With minutes</option></select></div></div>'''
    for year in sorted({m['date'][:4] for m in MEETINGS},reverse=True):
        body+=f'<section class="archive-year"><h2>{year}</h2>'
        for m in (m for m in MEETINGS if m['date'].startswith(year)):
            search=' '.join([m['date'],m['title']['th'],m['title']['en']]).lower()
            body+=f'<article class="meeting-row" data-meeting-search="{esc(search)}" data-has-minutes="{str(bool(m.get("minutes"))).lower()}"><div class="date-block"><time datetime="{esc(m["date"])}">{date_text(m["date"])}</time></div><div><span class="badge">{tr(m["format"])}</span><h3><a href="{meeting_url(m)}">{tr(m["title"])}</a></h3><div class="meta">{tr(m["time"])} · {tr(m["venue"])}</div><p class="summary">{tr(m["summary"])}</p><div class="row-links">{link(meeting_url(m),"เอกสารการประชุม →","Meeting resources →")}'
            if m.get('minutes'):
                mn=m['minutes']; label_th='รายงานการประชุม (ฉบับรับรอง)' if mn['status']=='approved' else 'รายงานการประชุม (ฉบับร่าง)'; label_en='Minutes (approved)' if mn['status']=='approved' else 'Minutes (draft)'
                body+=link(mn['url'],label_th,label_en)
            else: body+=f'<span class="meta">{pair("รายงานการประชุม: ยังไม่เผยแพร่","Minutes: not yet published")}</span>'
            body+='</div></div></article>'
        body+='</section>'
    body+=f'<div class="empty-state" id="archive-empty" hidden role="status"><p>{pair("ยังไม่มีการประชุมหรือรายงานที่ตรงกับตัวกรองนี้","No meetings or minutes match these filters.")}</p></div><p class="muted-note">{pair("เอกสารประกอบและร่างคำพูดใช้เตรียมการประชุม รายงานการประชุมจะระบุแยกต่างหาก พร้อมสถานะฉบับร่างหรือฉบับรับรอง","Briefing documents and speaking outlines are preparation materials. Minutes are listed separately and identified as draft or approved.")}</p></div></section>'
    page('meetings.html','meetings','คลังการประชุม','Meeting archive',body)


def detail(m):
    extras=f'<div class="meeting-information"><span>{date_text(m["date"])}</span><span>{tr(m["time"])}</span><span>{tr(m["venue"])}</span></div>'
    body=intro(m['title']['th'],m['title']['en'],m['summary'],('เอกสารการประชุม','MEETING RESOURCES'),extras)
    body+=f'<section class="section white"><div class="wrap"><div class="breadcrumbs">{link("meetings.html","← คลังการประชุม","← Meeting archive")}</div><div class="detail-layout"><div class="detail-main"><h2>{pair("เอกสารและเครื่องมือ","Documents & tools")}</h2>'
    for r in m['materials']:
        body+=f'<a class="resource-row" href="{safe_url(r["url"])}"><span class="file-type">{esc(r["type"])}</span><div><h3>{tr(r["title"])}</h3><p>{tr(r["detail"])}</p></div><span class="arrow" aria-hidden="true">↗</span></a>'
    body+=f'<section class="minutes"><h2>{pair("รายงานการประชุม","Meeting minutes")}</h2>'
    if m.get('minutes'):
        mn=m['minutes'];status=pair('ฉบับรับรอง','Approved') if mn['status']=='approved' else pair('ฉบับร่าง','Draft')
        body+=f'<p><span class="badge">{status}</span></p>'+link(mn['url'],'อ่านรายงานการประชุม','Read the minutes','button secondary')
        if mn.get('published_on'):body+=f'<p>{pair("เผยแพร่ ","Published ")}{date_text(mn["published_on"])}</p>'
    else:body+=f'<p>{pair("ยังไม่มีรายงานการประชุมเผยแพร่ในหน้านี้ เมื่อมีเอกสารที่พร้อมเผยแพร่ จะเพิ่มไว้ที่นี่พร้อมระบุสถานะและวันที่","No minutes have been published for this meeting. When available, they will be added here with their status and publication date.")}</p>'
    body+='</section></div><aside>'
    if m.get('registration_url'):
        body+=f'<section class="registration-box"><h2>{pair("ลงทะเบียนการประชุมครั้งนี้","Register for this meeting")}</h2><p>{date_text(m["date"])}</p>'
        if m.get('registration_qr'):body+=f'<img src="{safe_url(m["registration_qr"])}" alt="Registration QR for meeting {esc(m["date"])}" width="220" height="220">'
        body+=link(m['registration_url'],'เปิดแบบลงทะเบียน','Open registration form','button')+f'<p>{pair("บันทึกชื่อ สถาบัน และอีเมลสำหรับการประชุมครั้งนี้ ความยินยอมให้ติดต่อในอนาคตเป็นทางเลือก","Provide your name, institution and email for this meeting. Consent to future contact is optional.")}</p></section>'
    body+=f'<p class="muted-note">{pair("รายละเอียดเข้า Zoom อยู่ในคำเชิญประชุมเดิม","Zoom joining details are in the original meeting invitation.")}</p></aside></div></div></section>'
    page(meeting_url(m),'meetings',m['title']['th'],m['title']['en'],body)


def join():
    body=intro('เข้าร่วมเครือข่าย ECS','Join the ECS community',{'th':'ศึกษาการเป็นสมาชิก ECS และวิธียืนยันการเข้าร่วม Thailand Section','en':'Explore ECS membership and confirm your affiliation with Thailand Section.'})
    body+=f'''<section class="section white"><div class="wrap prose"><ol class="join-steps"><li><div><h2>{pair('เลือกประเภทสมาชิก ECS','Explore membership options')}</h2><p>{pair('ศึกษาประเภทสมาชิก คุณสมบัติ สิทธิประโยชน์ และค่าธรรมเนียมปัจจุบันจากเว็บไซต์ ECS','Review membership categories, eligibility, benefits and current fees on the ECS website.')}</p>{link(SECTION['membership_url'],'ข้อมูลการเป็นสมาชิก ECS ↗','ECS membership information ↗')}</div></li><li><div><h2>{pair('สมัครหรือต่ออายุผ่าน ECS','Join or renew through ECS')}</h2><p>{pair('ดำเนินการผ่านระบบสมาชิกของ ECS โดยตรง ระบบอาจให้เข้าสู่บัญชีหรือสร้างบัญชี ECS ก่อน','Use the official ECS membership portal. You may be asked to sign in or create an ECS account.')}</p>{link(SECTION['join_url'],'เปิดระบบสมัครสมาชิก ECS','Open the ECS membership portal','button')}</div></li><li><div><h2>{pair('ยืนยันการเข้าร่วม Thailand Section','Confirm your Thailand Section affiliation')}</h2><p>{pair('หากเป็นสมาชิกแล้วหรือต้องการคำแนะนำเกี่ยวกับการเข้าร่วม Thailand Section ติดต่อทีมบริการสมาชิกของ ECS','Existing members and those seeking help with Thailand Section affiliation can contact the ECS membership team.')}</p><a href="mailto:{esc(SECTION['affiliation_email'])}">{esc(SECTION['affiliation_email'])}</a></div></li></ol><p class="source-line">{pair('แหล่งข้อมูล: ','Sources: ')}{link(ANNOUNCEMENT,'ประกาศ ECS Thailand Section','ECS Thailand Section announcement')} · {link(SECTION['membership_url'],'ข้อมูลสมาชิก ECS','ECS membership information')}</p><p class="muted-note">{pair('การลงทะเบียนเข้าร่วมประชุมบนเว็บไซต์นี้เป็นคนละขั้นตอนกับการสมัครสมาชิก ECS และไม่ได้ยืนยันสิทธิ์ลงคะแนนเลือกตั้ง','Meeting registration on this website is separate from ECS membership and does not establish election voting eligibility.')}</p></div></section>'''
    page('join.html','join','เข้าร่วม ECS','Join ECS',body)


if __name__ == '__main__':
    validate()
    reserved = {route for route, _, _, _ in NAV} | {meeting_url(m) for m in MEETINGS}
    documents = [item for m in MEETINGS for item in m['materials'] + ([m['minutes']] if m.get('minutes') else [])]
    for item in documents:
        target = urlsplit(item['url'])
        if target.scheme or not target.path.endswith('.html') or target.path in reserved:
            continue
        filename=target.path
        rendered=ROOT/'published'/filename
        if rendered.is_file():
            (ROOT/filename).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(rendered,ROOT/filename)
        elif not (ROOT/filename).is_file(): raise SystemExit(f'Render or add the meeting document first: {filename}')
    home();about();activities();archive();join()
    for m in MEETINGS:detail(m)
    # Fail on missing local document destinations instead of publishing broken links.
    for m in MEETINGS:
        if m.get('registration_qr') and not (ROOT/m['registration_qr']).is_file(): raise SystemExit(f'Missing registration QR: {m["registration_qr"]}')
        for item in m['materials']+([m['minutes']] if m.get('minutes') else []):
            target=urlsplit(item['url'])
            if not target.scheme and not (ROOT/target.path).is_file():raise SystemExit(f'Missing document: {target.path}')
    print(f'Built 5 main pages and {len(MEETINGS)} meeting pages. Existing QR destinations preserved.')
