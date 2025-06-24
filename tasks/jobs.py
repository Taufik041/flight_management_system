from sqlmodel import Session, select
from database import engine
from schemas import User, TaskCompletion, PaymentLog
from utils.email import send_email
from logger import logger

# Track already-notified users to avoid duplicate notifications
notified_users = set()

def check_negative_balances():
    logger.info("🔁 Running hourly negative balance check...")

    with Session(engine) as session:
        users = session.exec(select(User).where(User.is_active == True)).all()

        for user in users:
            # Calculate balance
            payments = session.exec(
                select(PaymentLog).where(PaymentLog.user_id == user.id)
            ).all()
            completions = session.exec(
                select(TaskCompletion).where(TaskCompletion.user_id == user.id)
            ).all()

            balance = sum(p.amount for p in payments) - sum(c.charge_amount for c in completions)

            if balance < 0 and user.id not in notified_users:
                # Send email
                send_email(
                    to=user.email,
                    subject="⚠️ Negative Account Balance",
                    body=f"Hi {user.first_name},\n\nYour current balance is ₹{balance:.2f}. Please top-up your account to avoid disruption."
                )

                # Track notification
                notified_users.add(user.id)
                logger.info(f"📧 Sent negative balance alert to {user.email}")
