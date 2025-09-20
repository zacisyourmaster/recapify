import os
import secrets
import logging
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException, SpotifyOauthError
from sqlmodel import Session, select
from models import Users
from db import get_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Recapify App", version="0.1.0")

load_dotenv()

# Constants
SUCCESS_MESSAGE = "Signup complete! You can close this window."
ERROR_MESSAGES = {
    "no_code": "Authorization code not provided",
    "no_refresh_token": "No refresh token returned by Spotify",
    "profile_error": "Failed to get user profile from Spotify",
    "spotify_error": "Spotify API error occurred",
    "database_error": "Database operation failed",
}

# Validate environment variables
REQUIRED_ENV_VARS = [
    "CLIENT_ID",
    "CLIENT_SECRET",
    "REDIRECT_URI",
    "SCOPES",
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )


def create_spotify_oauth(state: Optional[str] = None) -> SpotifyOAuth:
    """Create SpotifyOAuth instance with consistent configuration."""
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope=os.getenv("SCOPES"),
        state=state,
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Spotify OAuth API is running"}


@app.get("/login")
async def login():
    """Initiate Spotify OAuth login flow."""
    try:
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(16)
        sp_oauth = create_spotify_oauth(state)
        auth_url = sp_oauth.get_authorize_url()

        logger.info("User initiated login flow")
        return RedirectResponse(auth_url)

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate login")


@app.get("/callback")
async def callback(request: Request, session: Session = Depends(get_session)):
    """Handle Spotify OAuth callback."""
    try:
        # Get authorization code
        code = request.query_params.get("code")
        if not code:
            logger.warning("Callback received without authorization code")
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES["no_code"])

        # Exchange code for tokens
        sp_oauth = create_spotify_oauth()
        try:
            token_info = sp_oauth.get_access_token(code)
        except SpotifyOauthError as e:
            logger.error(f"OAuth token exchange failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")

        if not token_info:
            logger.error("No refresh token received from Spotify")
            raise HTTPException(
                status_code=400, detail=ERROR_MESSAGES["no_refresh_token"]
            )
        # Extract tokens
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")

        # Get user profile
        try:
            sp = spotipy.Spotify(auth=access_token)
            user_profile = sp.current_user()
        except SpotifyException as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES["spotify_error"])

        if not user_profile or not user_profile.get("id"):
            logger.error("Invalid user profile received")
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES["profile_error"])

        # Extract user data
        user_id = user_profile.get("id")
        display_name = user_profile.get("display_name")
        email = user_profile.get("email")

        # Database operations
        try:
            # Check if user exists
            statement = select(Users).where(Users.spotify_user_id == user_id)
            existing_user = session.exec(statement).first()

            if existing_user:
                # Update existing user
                existing_user.access_token = access_token
                existing_user.refresh_token = refresh_token
                existing_user.display_name = display_name
                existing_user.email = email
                logger.info(f"Updated existing user: {user_id}")
            else:
                # Create new user
                new_user = Users(
                    spotify_user_id=user_id,
                    display_name=display_name,
                    email=email,
                    access_token=access_token,
                    refresh_token=refresh_token,
                )
                session.add(new_user)
                logger.info(f"Created new user: {user_id}")

            session.commit()

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            session.rollback()
            raise HTTPException(
                status_code=500, detail=ERROR_MESSAGES["database_error"]
            )

        # return RedirectResponse("http://localhost:5173/?logged_in=1")
        return RedirectResponse("https://recapify-site.onrender.com/?logged_in=1")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "environment_variables": {
            var: "Set" if os.getenv(var) else "Missing" for var in REQUIRED_ENV_VARS
        },
    }


# Error handlers


# Proper exception handlers returning JSONResponse
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )
