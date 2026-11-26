# GameLog

GameLog — мікроблог для геймерів: короткі дописи про ігри, у які ти зараз граєш, підписки на інших гравців, особисті повідомлення, сповіщення, експорт дописів і REST API.

Проєкт зроблено за [The Flask Mega-Tutorial (2024 Edition)](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) Мігеля Грінберга, розділи 1–23. Структура, моделі, міграції, blueprints, шаблони і команди такі самі, як у туторіалі. Змінено тільки тему (назву, тексти, назву черги RQ) і мову перекладу: українська замість іспанської.

## Швидкий старт (Windows, PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask db upgrade
flask translate compile
flask run
```

Сайт: http://localhost:5000. Змінні `FLASK_APP=gamelog.py` і `FLASK_DEBUG=1` вже записані у `.flaskenv`.

Тести: `python tests.py`

Shell з готовими імпортами (`db`, `sa`, `so`, `User`, `Post`, `Message`, `Notification`, `Task`): `flask shell`

## Змінні оточення (`.env`, розділ 15)

Файл `.env` у корені проєкту. Кожна змінна необов'язкова: без неї відповідна функція просто вимкнена, як і в туторіалі.

```
SECRET_KEY=щось-довге-і-випадкове
DATABASE_URL=sqlite:///app.db
MAIL_SERVER=localhost
MAIL_PORT=8025
MS_TRANSLATOR_KEY=<ключ Azure Translator>
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://
```

| Функція | Розділ | Як увімкнути |
|---|---|---|
| Листи (скидання пароля, помилки, експорт) | 7, 10 | Тестовий SMTP-сервер: `aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:8025`, а в `.env` прописати `MAIL_SERVER=localhost`, `MAIL_PORT=8025` |
| Переклад дописів (кнопка «Translate») | 14 | Ключ Azure Translator у `MS_TRANSLATOR_KEY` |
| Повнотекстовий пошук | 16 | `docker run --name elasticsearch -d --rm -p 9200:9200 --memory="2GB" -e discovery.type=single-node -e xpack.security.enabled=false -t docker.elastic.co/elasticsearch/elasticsearch:8.11.1`, у `.env` прописати `ELASTICSEARCH_URL=http://localhost:9200`, потім у `flask shell`: `Post.reindex()` |
| Фоновий експорт дописів | 22 | Redis (`docker run --name redis -d -p 6379:6379 redis:7`) і воркер `rq worker gamelog-tasks`. На Windows RQ-воркер не запускається (йому потрібен `fork`), тому його треба запускати у WSL або Docker. Без Redis кнопка «Export your posts» падає з помилкою з'єднання, у туторіалі так само |

## Переклади (розділ 13)

```
flask translate init <мова>    # додати нову мову
flask translate update         # після зміни текстів у коді
flask translate compile        # зібрати .mo
```

Мова інтерфейсу береться з налаштувань браузера (`Accept-Language`). Щоб побачити український переклад, постав українську першою мовою в браузері.

## API (розділ 23)

```
http --auth <user>:<password> POST http://localhost:5000/api/tokens
http GET http://localhost:5000/api/users/1 "Authorization:Bearer <token>"
http POST http://localhost:5000/api/users username=bob password=dog email=bob@example.com
```

Ендпоінти: `GET /api/users`, `GET /api/users/<id>`, `GET /api/users/<id>/followers`, `GET /api/users/<id>/following`, `POST /api/users`, `PUT /api/users/<id>`, `POST /api/tokens`, `DELETE /api/tokens`.

## Деплой (розділи 17–19)

- `deployment/nginx/gamelog`, `deployment/supervisor/gamelog.conf`, `deployment/supervisor/gamelog-tasks.conf`: деплой на Linux з nginx, gunicorn і supervisor (розділ 17). `Vagrantfile` для тестової Ubuntu VM.
- `Procfile`: Heroku (розділ 18).
- `Dockerfile` і `boot.sh`: Docker (розділ 19), `docker build -t gamelog:latest .`

## Що з якого розділу

| Розділ | Що зроблено | Де шукати |
|---|---|---|
| 1. Hello, World! | Flask-застосунок, `.flaskenv` | `gamelog.py`, `app/__init__.py` |
| 2. Templates | Jinja2, наслідування шаблонів | `app/templates/base.html`, `index.html` |
| 3. Web Forms | Flask-WTF, `Config` | `config.py`, `app/auth/forms.py` |
| 4. Database | Flask-SQLAlchemy, Flask-Migrate, моделі User і Post | `app/models.py`, `migrations/` |
| 5. User Logins | Flask-Login, хешування паролів, реєстрація | `app/auth/routes.py` |
| 6. Profile Page and Avatars | Профіль, Gravatar, `last_seen`, редагування профілю | `user.html`, `edit_profile.html` |
| 7. Error Handling | Сторінки 404 і 500, логування у файл і на пошту | `app/errors/` |
| 8. Followers | Підписки (many-to-many), стрічка від підписок | `followers` у `app/models.py` |
| 9. Pagination | Стрічка Explore, посторінковий вивід | `app/main/routes.py` |
| 10. Email Support | Flask-Mail, скидання пароля через JWT | `app/email.py`, `app/auth/email.py` |
| 11. Facelift | Bootstrap 5 | `base.html`, `bootstrap_wtf.html` |
| 12. Dates and Times | Flask-Moment | `_post.html`, `user.html` |
| 13. I18n and L10n | Flask-Babel, переклад `uk` | `app/translations/uk/`, `app/cli.py` |
| 14. Ajax | Визначення мови допису, переклад через Microsoft Translator | `app/translate.py` |
| 15. A Better Application Structure | Blueprints, application factory, `.env` | `app/main`, `app/auth`, `app/errors` |
| 16. Full-Text Search | Elasticsearch, `SearchableMixin` | `app/search.py` |
| 17–19. Deployment | Linux, Heroku, Docker | `deployment/`, `Procfile`, `Dockerfile` |
| 20. Some JavaScript Magic | Спливаюча картка користувача | `user_popup.html` |
| 21. User Notifications | Особисті повідомлення, лічильник сповіщень | `Message`, `Notification` |
| 22. Background Jobs | RQ, експорт дописів з прогресом | `app/tasks.py`, `Task` |
| 23. APIs | REST API, токени, Flask-HTTPAuth | `app/api/` |

## Відмінності від туторіалу

- Назва: `microblog.py` перейменовано на `gamelog.py`, `Microblog` на `GameLog`, черга `microblog-tasks` тепер `gamelog-tasks`. Підпис поля форми допису: «What are you playing?» замість «Say something».
- Мова перекладу українська (`uk`), а не іспанська (`es`).
- Версії пакетів у `requirements.txt` новіші, ніж у туторіалі (2023 рік): старі пакети не встановлюються на Python 3.14. `rq` закріплено на 1.x, бо код туторіалу викликає `job.get_id()`, а в RQ 2.x цього методу вже немає. `elasticsearch` закріплено на 8.x під сервер Elasticsearch 8.
