web: flask db upgrade; flask translate compile; gunicorn gamelog:app
worker: rq worker gamelog-tasks
