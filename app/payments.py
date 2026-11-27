"""Мок платіжного шлюзу для підписки GameLog Pro.

Справжніх грошей тут немає. Шлюз поводиться як тестовий режим Stripe:
- номер картки перетворюється на токен ще у веб-запиті (tokenize),
  а в чергу RQ і в базу потрапляють лише токен і останні 4 цифри;
- списання (charge) виконує фоновий воркер, воно триває кілька секунд
  і може завершитися відмовою залежно від тестової картки.
"""
import secrets
import time
from datetime import timedelta
from flask_babel import lazy_gettext as _l

PLANS = {
    'demo': {'name': _l('Demo (2 minutes)'), 'price': 1,
             'duration': timedelta(minutes=2)},
    'month': {'name': _l('1 month'), 'price': 99,
              'duration': timedelta(days=30)},
    'year': {'name': _l('1 year'), 'price': 899,
             'duration': timedelta(days=365)},
}

# тестові картки: номер -> токен, який далі обробляє шлюз
TEST_CARDS = {
    '6767676767676767': 'tok_success',
    '4000000000000002': 'tok_card_declined',
    '4000000000009995': 'tok_insufficient_funds',
}

ERRORS = {
    'tok_card_declined': 'Your card was declined.',
    'tok_insufficient_funds': 'Your card has insufficient funds.',
    'tok_unknown_card': 'Only test cards are accepted in test mode.',
}

PROCESSING_TIME = 3  # секунди, щоб у черзі було видно прогрес


class PaymentError(Exception):
    pass


def normalize_card_number(number):
    return ''.join(ch for ch in number if ch.isdigit())


def luhn_valid(number):
    # алгоритм Луна: контрольна сума, яку мають усі справжні номери карток
    digits = [int(d) for d in number]
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def tokenize(card_number):
    number = normalize_card_number(card_number)
    return TEST_CARDS.get(number, 'tok_unknown_card')


def charge(token, amount):
    """Імітує списання. Повертає id транзакції або кидає PaymentError."""
    time.sleep(PROCESSING_TIME)
    if token in ERRORS:
        raise PaymentError(ERRORS[token])
    if amount <= 0:
        raise PaymentError('Invalid amount.')
    return 'txn_' + secrets.token_hex(8)
