
# Recapify

A personal Spotify recap and reporting system. Users can sign up to receive weekly email reports of their Spotify listening habits.

## Project Structure

```shell

recapify/
│
├── app/                  # Core backend: ETL, DB, reporting logic
│   ├── __init__.py
│   ├── aggregator.py
│   ├── db.py
│   ├── generate_report.py
│   ├── pull_data.py
│   ├── send_email.py
│
├── api/                  # FastAPI app (user signup, endpoints)
│   ├── __init__.py
│   ├── main.py           # FastAPI entrypoint
│   ├── routes.py         # API routes (e.g., /signup)
│   ├── models.py         # Pydantic models for request/response
│   ├── dependencies.py   # DB/session helpers, shared logic
│
├── templates/
│   └── weekly_report.html
│
├── requirements.txt
├── send_report.py        # Batch runner for sending emails
├── run_etl.py            # Batch runner for ETL
└── README.md
```

## Features

- Weekly Spotify recap emails for users
- ETL pipeline to aggregate listening data
- FastAPI backend for user signup and API endpoints
- Jinja2 templating for HTML reports

## Setup

1. **Clone the repo:**

   ```pwsh
   git clone <your-repo-url>
   cd recapify
   ```

2. **Install dependencies:**

   ```pwsh
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Create a `.env` file in the root directory with:
  
    ```python
     DB_HOST=localhost
     DB_PORT=5432
     DB_NAME=spotify
     DB_USER=postgres
     DB_PASSWORD=yourpassword
     SENDGRID_API_KEY=your_sendgrid_key
     EMAIL_ADDR=your_from_email@example.com
     ```

4. **Set up the database:**

   ```pwsh
   python app/pull_data.py  # or run_etl.py if you have a setup step
   ```

5. **Create the email template:**
   - Edit `templates/weekly_report.html` to customize your report.

## Running the Batch Jobs

- **Send weekly reports:**
  
  ```pwsh
  python send_report.py
  ```

- **Run ETL pipeline:**

  ```pwsh
  python run_etl.py
  ```

## Running the API Server

- **Start FastAPI server:**
  
  ```pwsh
  uvicorn api.main:app --reload
  ```

## Adding Users via API

- POST to `/signup` endpoint with Spotify info and email.
- See `api/routes.py` for details.

## License

MIT

## Author

Zach Smith
