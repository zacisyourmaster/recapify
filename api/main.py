import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from app.pull_data import get_spotify_client, get_current_user
from app.db import upsert_user, get_conn
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fastapi.responses import RedirectResponse

app = FastAPI()

load_dotenv()


@app.get("/")
async def root():
    return {"a": "message"}


# Spotify OAuth endpoints
@app.get("/login")
async def login():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=os.getenv("SCOPES"),
    )
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)


@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=os.getenv("SCOPES"),
    )
    token_info = sp_oauth.get_access_token(code)
    refresh_token = token_info.get("refresh_token")
    access_token = token_info.get("access_token")
    if not refresh_token:
        return {"error": "No refresh token returned by Spotify"}
    # Get user profile with Spotipy
    sp = spotipy.Spotify(auth=access_token)
    user_profile = sp.current_user()

    assert user_profile is not None

    user_id = user_profile.get("id")
    display_name = user_profile.get("display_name")
    email = user_profile.get("email")
    # Save user to DB
    conn = get_conn()
    upsert_user(
        conn=conn,
        spotify_user_id=user_id,
        display_name=display_name,
        email=email,
        refresh_token=refresh_token,
    )
    return {"message": "Signup complete! You can close this window."}
