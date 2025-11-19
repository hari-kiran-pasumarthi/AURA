from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from backend.services.mail_config import conf
from fastapi_mail import FastMail, MessageSchema
from datetime import datetime

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.start()


# =========================================================
# EMAIL UTIL: Send any email
# =========================================================
async def send_email(email: str, subject: str, body: str):
    fm = FastMail(conf)

    msg = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="html",
    )

    await fm.send_message(msg)


# =========================================================
# TASK REMINDER (already working)
# =========================================================
def schedule_task(email: str, task_name: str, run_time: datetime):
    trigger = DateTrigger(run_date=run_time)

    scheduler.add_job(
        send_email,
        trigger=trigger,
        args=[
            email,
            "⏰ AURA Task Reminder",
            f"<p>Your task <b>{task_name}</b> is starting now!</p>",
        ],
    )

    print(f"⏰ Scheduled reminder for {email} at {run_time}")


# =========================================================
# DAILY SUMMARY (NEW)
# =========================================================
def schedule_daily_summary(email: str, date_str: str, blocks: list):
    """
    Sends a daily summary email at 07:00 AM on the given date.
    """

    try:
        run_time = datetime.fromisoformat(f"{date_str}T07:00:00")

        # Build tasks list HTML
        if blocks:
            items = "<ul>"
            for b in blocks:
                items += f"<li><b>{b.get('task','Task')}</b> — {b.get('start_time')} to {b.get('end_time')}</li>"
            items += "</ul>"
        else:
            items = "<p>No planned sessions today.</p>"

        subject = f"📅 AURA | Your Study Plan for {date_str}"

        body = f"""
            <h3>🧠 AURA Daily Study Summary</h3>
            <p>Here is your study plan for <b>{date_str}</b>:</p>
            {items}
            <hr>
            <p>Stay consistent — you've got this 💪</p>
        """

        job_id = f"summary_{email}_{date_str}"

        scheduler.add_job(
            send_email,
            trigger=DateTrigger(run_date=run_time),
            args=[email, subject, body],
            id=job_id,
            replace_existing=True,
        )

        print(f"📨 Daily summary scheduled for {email} on {date_str} at 07:00 AM")

    except Exception as e:
        print(f"❌ Failed to schedule summary: {e}")
