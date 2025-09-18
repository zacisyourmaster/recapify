# Work in progress
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os
from datetime import date

from .db import get_all_users
from .generate_report import generate_user_weekly_report

load_dotenv()


def send_report(email: str, display_name: str, html_content: str):
    """Send a single report to a user."""
    message = Mail(
        from_email=os.getenv("EMAIL_ADDR"),
        to_emails=email,
        subject=f"Hey, {display_name}. Your Weekly Report Card is Ready!",
        html_content=html_content,
    )

    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)
    return (response.status_code, response.body)


def send_reports_for_all_users():
    """
    Loops over all users in DB, generates their weekly report,
    and sends it via SendGrid.
    """
    today = date.today()
    year, week, _ = today.isocalendar()
    users = get_all_users()
    print(f"Found {len(users)} users in DB.")

    for user in users:
        user_id = user["id"]
        email = user["email"]
        display_name = user["display_name"]
        if not email:
            print(f"⚠️ Skipping user id={user_id} (no email on file)")
            continue
        try:
            html_content = generate_user_weekly_report(user_id, year, week)
            status = send_report(
                email=email, display_name=display_name, html_content=html_content
            )
            print(f"✅ Sent report to {display_name} ({email}) — Status {status[0]}")
        except Exception as e:
            print(f"❌ Failed to send report to {display_name} ({email}): {e}")


def main():
    send_reports_for_all_users()


if __name__ == "__main__":
    main()
