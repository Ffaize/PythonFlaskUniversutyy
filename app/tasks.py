import json
import sys
import time
from datetime import timedelta
import sqlalchemy as sa
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User, Post, Task, ScheduledPost, Payment
from app.email import send_email
from app import payments

app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = db.session.get(Task, job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_posts(user_id):
    try:
        user = db.session.get(User, user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = db.session.scalar(sa.select(sa.func.count()).select_from(
            user.posts.select().subquery()))
        for post in db.session.scalars(user.posts.select().order_by(
                Post.timestamp.asc())):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)

        send_email(
            '[GameLog] Your game posts',
            sender=app.config['ADMINS'][0], recipients=[user.email],
            text_body=render_template('email/export_posts.txt', user=user),
            html_body=render_template('email/export_posts.html', user=user),
            attachments=[('posts.json', 'application/json',
                          json.dumps({'posts': data}, indent=4))],
            sync=True)
    except Exception:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)


def publish_scheduled_post(scheduled_post_id):
    # запускається планувальником RQ у час, вибраний користувачем
    scheduled_post = db.session.get(ScheduledPost, scheduled_post_id)
    if scheduled_post is None:
        return  # пост скасували, публікувати нічого
    scheduled_post.publish()
    db.session.commit()


def send_notification_email(user_id, subject, template, context):
    user = db.session.get(User, user_id)
    if user is None or not user.email_notifications:
        return
    send_email(
        subject,
        sender=app.config['ADMINS'][0], recipients=[user.email],
        text_body=render_template(f'email/{template}.txt', user=user,
                                  **context),
        html_body=render_template(f'email/{template}.html', user=user,
                                  **context),
        sync=True)


def process_payment(user_id, payment_id, card_token):
    try:
        _set_task_progress(0)
        user = db.session.get(User, user_id)
        payment = db.session.get(Payment, payment_id)
        _set_task_progress(30)
        try:
            payment.transaction_id = payments.charge(card_token,
                                                     payment.amount)
        except payments.PaymentError as e:
            payment.status = 'failed'
            payment.error = str(e)
            db.session.commit()
            send_email(
                '[GameLog] Payment failed',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/payment_failed.txt',
                                          user=user, payment=payment),
                html_body=render_template('email/payment_failed.html',
                                          user=user, payment=payment),
                sync=True)
            return
        _set_task_progress(70)
        payment.status = 'succeeded'
        pro_until = user.extend_pro(payments.PLANS[payment.plan]['duration'])
        db.session.commit()
        # окрема задача в черзі, яку планувальник запустить, коли Pro закінчиться;
        # +1 секунда, бо планувальник RQ округлює час до цілих секунд
        app.task_queue.enqueue_at(pro_until + timedelta(seconds=1),
                                  'app.tasks.subscription_expired', user.id)
        send_email(
            '[GameLog] Your GameLog Pro receipt',
            sender=app.config['ADMINS'][0], recipients=[user.email],
            text_body=render_template('email/payment_receipt.txt',
                                      user=user, payment=payment),
            html_body=render_template('email/payment_receipt.html',
                                      user=user, payment=payment),
            sync=True)
    except Exception:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)


def subscription_expired(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.is_pro():
        return  # підписку вже продовжили
    send_email(
        '[GameLog] Your GameLog Pro subscription has expired',
        sender=app.config['ADMINS'][0], recipients=[user.email],
        text_body=render_template('email/subscription_expired.txt',
                                  user=user),
        html_body=render_template('email/subscription_expired.html',
                                  user=user),
        sync=True)
