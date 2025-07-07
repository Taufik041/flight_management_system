from sqlmodel import Session, select
from database import engine
from schemas import User, TaskCompletion, PaymentLog, Notification
from utils.email import send_email
from logger import logger

def check_negative_balances():
    logger.info("🔁 Running hourly negative balance check...")

    with Session(engine) as session:
        users = session.exec(select(User).where(User.is_active == True)).all()

        for user in users:
            payments = session.exec(
                select(PaymentLog).where(PaymentLog.user_id == user.id)
            ).all()
            completions = session.exec(
                select(TaskCompletion).where(TaskCompletion.user_id == user.id)
            ).all()

            task_charges = sum(c.charge_amount for c in completions)
            flight_charges = sum((c.flight_time / 60) * 1000 for c in completions)
            total_charges = task_charges + flight_charges
            total_paid = sum(p.amount for p in payments)
            
            balance = total_paid - total_charges

            # Only notify if negative and not already notified
            if balance < 0:
                existing = session.exec(
                    select(Notification).where(
                        Notification.user_id == user.id,
                        Notification.type == "negative_balance"
                    )
                ).first()

                if not existing:
                    # Send email
                    send_email(
                        to=user.email,
                        subject="⚠️ Negative Account Balance",
                        body=(
                            f"Hi {user.first_name},\n\n"
                            f"Your current balance is ₹{balance:.2f}. "
                            "Please top-up your account to avoid disruption.\n\n"
                            "Thanks,\nTeam"
                        )
                    )

                    # Save notification
                    if user.id is not None:  # Ensure user.id is not None
                        notif = Notification(
                            user_id=user.id,
                            title="Negative Balance Alert",
                            message=f"Your balance is ₹{balance:.2f}. Please add funds.",
                            type="negative_balance"
                        )
                    session.add(notif)
                    session.commit()

                    logger.info(f"📧 Sent negative balance alert to {user.email}")
