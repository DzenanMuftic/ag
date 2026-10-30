#!/usr/bin/env python3
"""Daily email check -> Telegram alerts + DeepSeek Bosnian sales reply for info@asistentica.online."""
import imaplib, email, json, os, re, smtplib, sys, time, urllib.request
from email.header import decode_header
from email.mime.text import MIMEText
from email.utils import formatdate, parseaddr

# Load settings from a .env file in the same directory, if present
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
except Exception:
    pass

CFG = {
    'imap_host': os.environ.get('EMAIL_IMAP_HOST', 'mail.privateemail.com'),
    'email': os.environ.get('EMAIL_USER', 'info@asistentica.online'),
    'password': os.environ.get('EMAIL_PASSWORD', ''),
    'tg_token': os.environ.get('TG_TOKEN', ''),
    'tg_chat': os.environ.get('TG_CHAT', ''),
    'deepseek_key': os.environ.get('DEEPSEEK_KEY', ''),
    'deepseek_model': os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
    'smtp_host': os.environ.get('SMTP_HOST', 'mail.privateemail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', '465')),
    'auto_send': os.environ.get('AUTO_SEND', 'false').lower() == 'true',
}

KEYWORDS = [
    'action required', 'verification code', 'verify your', 'suspended',
    'deactivated', 'has been disabled', 'blocked', 'unauthorized',
    'unusual activity', 'new sign-in', 'sign-in attempt', 'password reset',
    'invoice', 'payment failed', 'payment due', 'overdue', 'terminated',
    'security alert', 'breach', 'compromised', 'hacked',
    'marked inactive', 'mark inactive',
]

IMPORTANT_SENDERS = [
    'account-alerts@t.brevo.com', 'mailer-daemon', 'pesupport@namecheap.com',
]

BLOCKLIST = [
    'welcome@t.brevo.com', 'campaigns@m.brevo.com', '@info.n8n.io',
    '@e.mailchimp.com', 'google-noreply@google.com', '@thefini-newsletter.com',
    'hello@e.mailchimp.com',
]

STATE = os.path.expanduser('~/.email-alerts-state')
LOG = os.path.expanduser('~/.email-alerts.log')
LOCK = os.path.expanduser('~/.email-alerts.lock')
DRY = '--dry-run' in sys.argv


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line)
    try:
        with open(LOG, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass


def dec(s):
    if not s:
        return ''
    out = ''
    for t, enc in decode_header(s):
        out += t.decode(enc or 'utf-8', errors='replace') if isinstance(t, bytes) else t
    return out.strip()


def send_tg(text):
    url = f"https://api.telegram.org/bot{CFG['tg_token']}/sendMessage"
    for i in range(0, len(text), 4000):
        chunk = text[i:i + 4000]
        data = json.dumps({'chat_id': CFG['tg_chat'], 'text': chunk}).encode()
        urllib.request.urlopen(
            urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}),
            timeout=25,
        )


def strip_html(html):
    html = re.sub(r'<style.*?</style>', ' ', html, flags=re.S | re.I)
    html = re.sub(r'<script.*?</script>', ' ', html, flags=re.S | re.I)
    html = re.sub(r'<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', html).strip()


def extract_text(msg, limit=4000):
    parts = []
    if msg.is_multipart():
        for p in msg.walk():
            if p.get_content_type() == 'text/plain':
                try:
                    t = p.get_payload(decode=True)
                    if t:
                        parts.append(t.decode(p.get_content_charset() or 'utf-8', errors='replace'))
                except Exception:
                    pass
            elif p.get_content_type() == 'text/html' and not parts:
                try:
                    t = p.get_payload(decode=True)
                    if t:
                        parts.append(strip_html(t.decode(p.get_content_charset() or 'utf-8', errors='replace')))
                except Exception:
                    pass
    else:
        try:
            t = msg.get_payload(decode=True)
            if t:
                ct = msg.get_content_type()
                raw = t.decode(msg.get_content_charset() or 'utf-8', errors='replace')
                parts.append(strip_html(raw) if ct == 'text/html' else raw)
        except Exception:
            pass
    text = '\n\n'.join(p for p in parts if p and p.strip()).strip()
    return text[:limit]


def deepseek_reply(subject, sender, body_text):
    system = (
        "You are a professional, friendly sales representative for the company Asistentica. "
        "Always write your reply in BOSNIAN language. Be polite, concise and helpful."
    )
    user = (
        f"Write a reply email to this customer message.\n\n"
        f"From: {sender}\nSubject: {subject}\n\nMessage:\n{body_text}\n\n"
        f"Write ONLY the reply email text in Bosnian."
    )
    url = "https://api.deepseek.com/chat/completions"
    payload = json.dumps({
        "model": CFG['deepseek_model'],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CFG['deepseek_key']}",
    })
    resp = urllib.request.urlopen(req, timeout=90)
    data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"].strip()


def send_email_reply(to_addr, subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = CFG['email']
    msg['To'] = to_addr
    msg['Subject'] = ('Re: ' + subject)[:200]
    msg['Date'] = formatdate(localtime=True)
    server = smtplib.SMTP_SSL(CFG['smtp_host'], CFG['smtp_port'], timeout=30)
    server.login(CFG['email'], CFG['password'])
    server.sendmail(CFG['email'], [to_addr], msg.as_string())
    server.quit()


def is_important(subject, sender, body_bytes):
    low_sender = sender.lower()
    # newsletters / marketing are never "important"
    if any(b in low_sender for b in BLOCKLIST):
        return False
    # critical system senders (bounces, service alerts, support)
    if any(x in low_sender for x in IMPORTANT_SENDERS):
        return True
    # action-required keywords in subject
    if any(k in subject.lower() for k in KEYWORDS):
        return True
    # action-required keywords in body preview
    if body_bytes:
        lb = body_bytes.lower()
        if any(k.encode() in lb for k in KEYWORDS):
            return True
    return False


def main():
    log('start')
    if os.path.exists(LOCK):
        try:
            if time.time() - os.path.getmtime(LOCK) < 600:
                log('skip: another instance running')
                return
        except Exception:
            pass
    try:
        open(LOCK, 'w').close()
    except Exception:
        pass
    M = imaplib.IMAP4_SSL(CFG['imap_host'], 993)
    M.login(CFG['email'], CFG['password'])
    M.select('INBOX')

    typ, d = M.search(None, 'UNSEEN')
    uids = [u.decode() for u in d[0].split()]
    total_unread = len(uids)

    seen = set()
    if os.path.exists(STATE):
        seen = set(open(STATE).read().split())

    important = []
    for uid in uids:
        try:
            typ, hd = M.fetch(uid, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
            msg = email.message_from_bytes(hd[0][1])
            subject = dec(msg.get('Subject', '(no subject)'))
            sender = dec(msg.get('From', ''))
            date = (msg.get('Date', '') or '')[:25].strip()

            typ, bd = M.fetch(uid, '(BODY.PEEK[TEXT]<0.4096>)')
            preview = b''
            if bd and bd[0] and isinstance(bd[0], tuple) and bd[0][1]:
                preview = bd[0][1]
        except Exception as e:
            log(f'fetch {uid} failed: {e}')
            continue

        if not (is_important(subject, sender, preview) and uid not in seen):
            continue

        # only fetch the full message for emails we will reply to
        body_text = ''
        try:
            typ, full = M.fetch(uid, '(RFC822.PEEK)')
            body_text = extract_text(email.message_from_bytes(full[0][1]))
        except Exception as e:
            log(f'full fetch {uid} failed: {e}')

        important.append((uid, subject, sender, date, body_text))

    M.logout()

    log(f'unread={total_unread} important_new={len(important)}')

    if important:
        lines = ['⚠️ Important email(s) — info@asistentica.online', '']
        alerted = set()
        for i, (uid, subj, frm, date, body_text) in enumerate(important, 1):
            lines.append(f'{i}. {subj}')
            lines.append(f'   From: {frm}')
            lines.append(f'   Date: {date}')
            lines.append('')
            reply = ''
            try:
                reply = deepseek_reply(subj, frm, body_text or '(no body)')
                lines.append('   ✍️ Prijedlog odgovora (DeepSeek):')
                lines.append('   ' + reply.replace('\n', '\n   '))
            except Exception as e:
                log(f'deepseek failed for {uid}: {e}')
                lines.append('   ✍️ (odgovor nije generisan — greška)')
            lines.append('')
            if CFG['auto_send'] and not DRY and reply:
                to_addr = parseaddr(frm)[1]
                try:
                    send_email_reply(to_addr, subj, reply)
                    log(f'auto-replied to {to_addr}')
                    lines.append('   📤 Poslano (auto-send)')
                except Exception as e:
                    log(f'smtp failed for {to_addr}: {e}')
                    lines.append('   ⚠️ Auto-send nije uspio')
                lines.append('')
            alerted.add(uid)

        text = '\n'.join(lines).strip()
        if DRY:
            print('--- DRY RUN (not sent) ---')
            print(text)
        else:
            send_tg(text)
            log(f'sent {len(important)} important alerts to Telegram')
            new = seen | alerted
            with open(STATE, 'w') as f:
                f.write('\n'.join(sorted(new)))
    else:
        log('nothing important; no message sent')

    log('done')
    try:
        os.remove(LOCK)
    except Exception:
        pass


if __name__ == '__main__':
    main()
