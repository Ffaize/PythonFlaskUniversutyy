from flask import render_template, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from flask_babel import _
import redis
from app import db
from app.billing import bp
from app.billing.forms import CheckoutForm
from app.models import Payment
from app import payments


@bp.route('/')
@login_required
def subscription():
    payment_history = db.session.scalars(current_user.get_payments()).all()
    return render_template('billing/subscription.html', title=_('GameLog Pro'),
                           plans=payments.PLANS, payments=payment_history)


@bp.route('/checkout/<plan>', methods=['GET', 'POST'])
@login_required
def checkout(plan):
    if plan not in payments.PLANS:
        abort(404)
    form = CheckoutForm()
    if form.validate_on_submit():
        if current_user.get_task_in_progress('process_payment'):
            flash(_('A payment is already being processed.'))
            return redirect(url_for('billing.subscription'))
        number = payments.normalize_card_number(form.card_number.data)
        # далі працюємо лише з токеном: номер картки не зберігається
        token = payments.tokenize(number)
        payment = Payment(user=current_user, plan=plan,
                          amount=payments.PLANS[plan]['price'],
                          card_last4=number[-4:])
        db.session.add(payment)
        db.session.commit()
        try:
            current_user.launch_task('process_payment',
                                     _('Processing payment...'),
                                     payment.id, token)
        except redis.exceptions.RedisError:
            payment.status = 'failed'
            payment.error = 'Payment service is not available.'
            db.session.commit()
            flash(_('The task queue is not available, please try again '
                    'later.'))
            return redirect(url_for('billing.subscription'))
        db.session.commit()
        flash(_('Your payment is being processed.'))
        return redirect(url_for('billing.subscription'))
    return render_template('billing/checkout.html', title=_('Checkout'),
                           form=form, plan=payments.PLANS[plan])
