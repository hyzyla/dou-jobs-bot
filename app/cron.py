import atexit
import requests

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pytz import utc

from app.contants import HOST
from app import scheduler, app, parser, sender, db


def configure_scheduler():
    jobstores = {
        'default': SQLAlchemyJobStore(
            url=app.config['SQLALCHEMY_DATABASE_URI'],
            engine_options={'pool_size': 2},
        )
    }

    scheduler.add_job(func=job, trigger="interval", minutes=5)
    scheduler.configure(jobstores=jobstores, timezone=utc)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


def job():
    # trigger host for preventing sleeping, can be safety removed on production.
    requests.get(HOST)

    parser.get_new_vacancies()
    sender.dispatch_vacancies()
    sender.send_vacancies()
    db.session.close()
