from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from backend.services.mail_config import conf
from fastapi_mail import FastMail, MessageSchema
from datetime import datetime

scheduler = AsyncIOScheduler()
scheduler.start()

async def send_notification(email: str, message: str):
    fm = FastMail(conf)
    mail = MessageSchema(
        subject="⏰ AURA Task Reminder",
        recipients=[email],
        body=f"<p>{message}</p>",
        subtype="html",
    )
    await fm.send_message(mail)

def schedule_task(email: str, task_name: str, run_time: datetime):
    # Create trigger
    trigger = DateTrigger(run_date=run_time)

    # Add job
    scheduler.add_job(
        send_notification,
        trigger=trigger,
        args=[email, f"Your task '{task_name}' is starting now!"],
    )
