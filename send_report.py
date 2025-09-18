import logging
from app.send_email import send_reports_for_all_users
from app.generate_report import ensure_template_dir_exists


logging.basicConfig(level=logging.INFO)


def main():
    logging.info("Starting weekly Spotify report job...")

    # Ensure template exists
    if not ensure_template_dir_exists():
        logging.error("Template not found. Aborting send.")
        return

    # Send personalized HTML emails to all users
    send_reports_for_all_users()

    logging.info("Weekly Spotify report sent successfully.")


if __name__ == "__main__":
    main()
