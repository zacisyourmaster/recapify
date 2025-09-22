import os
import logging
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from . import db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("pull_data.log"), logging.StreamHandler()],
)


def get_current_user(sp) -> dict | None:
    """Get the current user's information from Spotify."""
    try:
        user_info = sp.current_user()
        return user_info
    except Exception as e:
        logging.error(f"Error fetching user info: {e}")
        return None


def user_exists(user_id, conn=None):
    """Check if a user exists in the database."""
    close_conn = False
    if conn is None:
        conn = db.get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE spotify_user_id = %s", (user_id,)
            )
            result = cur.fetchone()
            exists = result is not None and result[0] > 0
            return exists
    except Exception as e:
        logging.error(f"Error checking if user exists: {e}")
        return False
    finally:
        if close_conn and conn:
            conn.close()


def add_user(user_id, display_name, email, conn=None):
    """Add a user to the database."""
    close_conn = False
    if conn is None:
        conn = db.get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (spotify_user_id, display_name, email) 
                VALUES (%s, %s, %s) ON CONFLICT (spotify_user_id) DO NOTHING""",
                (user_id, display_name, email),
            )
            if close_conn:
                conn.commit()
            return True
    except Exception as e:
        logging.error(f"Error adding user to database: {e}")
        if close_conn:
            conn.rollback()
        return False
    finally:
        if close_conn and conn:
            conn.close()


def get_artist_image_url(sp: Spotify, artist_id) -> str:
    try:
        artist_info = sp.artist(artist_id=artist_id)
        artist_image_url = ""

        if artist_info and artist_info.get("images"):
            artist_image_url = artist_info["images"][0]["url"]

        return artist_image_url
    except Exception as e:
        logging.error(f"Error fetching artist image: {e}")
        return ""


def get_spotify_client(user=None):
    """Initialize and return a Spotify client."""
    load_dotenv()

    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")

    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        logging.error("Missing Spotify credentials. Check your .env file.")
        raise ValueError("Missing Spotify credentials. Check your .env file.")

    scope = "user-top-read user-read-recently-played user-read-private user-read-email"

    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
        cache_path=None,
    )
    if user and user.get("refresh_token"):
        logging.info(f"Refreshing token for {user['spotify_user_id']}")

        new_token_info = sp_oauth.refresh_access_token(user["refresh_token"])

        return Spotify(auth=new_token_info["access_token"])
    return Spotify(auth_manager=sp_oauth)


def fetch_data():
    conn = None
    try:
        conn = db.get_conn()
        users = db.get_all_users(conn=conn)

        # Get current Spotify user profile
        for user in users:
            try:
                sp = get_spotify_client(user=user)
                user_profile = get_current_user(sp)
                if not user_profile or not user_profile.get("id"):
                    logging.error(
                        f"Could not fetch user profile from Spotify for user {user.get('spotify_user_id', 'unknown')}."
                    )
                    continue

                # Fetch recent plays
                recent = sp.current_user_recently_played()
                if not recent or not recent.get("items"):
                    logging.info(
                        f"No recent plays found for user {user['spotify_user_id']}."
                    )
                    continue

                # Process each recently played track
                for item in recent["items"]:
                    track = item["track"]
                    artist = track["artists"][0]

                    artist_id = artist["id"]
                    artist_name = artist["name"]

                    track_id = track["id"]
                    track_name = track["name"]
                    album_image_url = (
                        track["album"]["images"][0]["url"]
                        if track["album"]["images"]
                        else None
                    )

                    try:
                        # Upsert artist and track
                        artist_image_url = get_artist_image_url(
                            sp=sp, artist_id=artist_id
                        )

                        db.upsert_artist(
                            conn,
                            artist_id=artist_id,
                            name=artist_name,
                            user_id=user["id"],
                            artist_image_url=artist_image_url,
                        )
                        db.upsert_track(
                            conn,
                            track_id=track_id,
                            user_id=user["id"],
                            name=track_name,
                            artist_id=artist_id,
                            album_image_url=album_image_url,
                        )

                        # Insert play
                        played_at = item["played_at"]
                        db.insert_play(
                            conn,
                            user_id=user["id"],
                            track_id=track_id,
                            played_at=played_at,
                        )

                    except Exception as e:
                        logging.error(
                            f"Error inserting data for track {track_name}: {e}"
                        )

                logging.info(
                    f"Successfully updated plays for user {user['display_name']} ({user['spotify_user_id']})"
                )

            except Exception as e:
                logging.error(
                    f"Error processing user {user.get('spotify_user_id', 'unknown')}: {e}"
                )
                continue

        # Commit all changes after processing all users
        if conn:
            conn.commit()
            logging.info("All data committed successfully")

    except Exception as e:
        logging.error(f"Error fetching Spotify data: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        # Close connection in finally block
        if conn:
            conn.close()


def main():
    try:
        logging.info("Initializing DB")
        db.init_db()
        logging.info("DB initialized")
    except Exception as e:
        logging.error(f"Error initializing DB: {e}")

    fetch_data()


if __name__ == "__main__":
    main()
