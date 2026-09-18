"""In-app notifications (always on) + optional email delivery.

Email is sent only when SMTP settings are present in the environment:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_FROM
Without them, in-app bell notifications still work — email is silently skipped.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from models import db, Notification, User


def _email_enabled():
    return all(os.environ.get(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"))


def _send_email(to_addr, subject, body):
    if not _email_enabled():
        return False
    try:
        msg = EmailMessage()
        msg["From"] = os.environ.get("MAIL_FROM", os.environ["SMTP_USER"])
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        host = os.environ["SMTP_HOST"]
        port = int(os.environ["SMTP_PORT"])
        ctx = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=15) as s:
                s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as s:
                s.starttls(context=ctx)
                s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
                s.send_message(msg)
        return True
    except Exception as e:  # never break the request over a mail failure
        print("[mail] failed:", e)
        return False


def notify(user_id, message, link=None, kind="info", email_subject=None):
    """Create an in-app notification and (if configured) email the user."""
    n = Notification(user_id=user_id, message=message, link=link, kind=kind)
    db.session.add(n)
    db.session.commit()
    user = User.query.get(user_id)
    if user and email_subject:
        base = os.environ.get("APP_BASE_URL", "").rstrip("/")
        full = (base + link) if (base and link) else (link or "")
        body = f"{message}\n\n{full}\n\n— M³ (ML Math Maxx)"
        _send_email(user.email, email_subject, body)


def notify_all_except(exclude_user_id, message, link=None, kind="info", email_subject=None):
    for u in User.query.filter(User.id != exclude_user_id).all():
        notify(u.id, message, link=link, kind=kind, email_subject=email_subject)
