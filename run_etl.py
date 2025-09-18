import logging
from app import pull_data

logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Starting daily Spotify ETL job...")
    pull_data.main()
    logging.info("Daily ETL job finished successfully.")

if __name__ == "__main__":
    main()
