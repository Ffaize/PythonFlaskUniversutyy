from threading import Thread
import redis
from flask import current_app
from flask_mail import Message
from app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body,
               attachments=None, sync=False):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()


def queue_notification_email(user, subject, template, **context):
    # лист відправляє воркер RQ, тому сторінка не чекає на SMTP-сервер
    if not user.email_notifications:
        return
    try:
        current_app.task_queue.enqueue('app.tasks.send_notification_email',
                                       user.id, subject, template, context)
    except redis.exceptions.RedisError:
        current_app.logger.warning(
            'Task queue is not available, email notification skipped')
