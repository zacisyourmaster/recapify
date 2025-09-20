import psycopg2
from dotenv import load_dotenv
import os
from typing import Optional
from psycopg2.extras import execute_values

load_dotenv()


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "spotify"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


# Functions for pull_data.py


def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      spotify_user_id TEXT UNIQUE NOT NULL,
      email TEXT,
      display_name TEXT,
      access_token TEXT,
      refresh_token TEXT
    );

    CREATE TABLE IF NOT EXISTS artists (
      id TEXT NOT NULL,                -- Spotify artist id
      user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      image_url TEXT,
      count INT DEFAULT 0,
      PRIMARY KEY (id, user_id)
    );

    CREATE TABLE IF NOT EXISTS tracks (
      id TEXT NOT NULL,                -- Spotify track id
      user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      artist_id TEXT NOT NULL,         -- links to Spotify artist id
      album_image TEXT,
      count INT DEFAULT 0,
      PRIMARY KEY (id, user_id),
      FOREIGN KEY (artist_id, user_id) REFERENCES artists(id, user_id)
    );
    
    CREATE TABLE IF NOT EXISTS plays (
      id SERIAL PRIMARY KEY,
      user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      track_id TEXT NOT NULL,
      played_at TIMESTAMP NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_plays_user_week ON plays (user_id, played_at);
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(ddl)
        conn.commit()


def upsert_user(
    conn,
    spotify_user_id: str,
    display_name: Optional[str],
    email: Optional[str],
    refresh_token: str,
) -> int:
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (spotify_user_id, display_name, email, refresh_token)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (spotify_user_id) DO UPDATE
                SET display_name = EXCLUDED.display_name,
                    email = EXCLUDED.email,
                    refresh_token = EXCLUDED.refresh_token
                RETURNING id
                """,
                (spotify_user_id, display_name, email, refresh_token),
            )
            result = cur.fetchone()
            if result is None:
                raise Exception("Failed to upsert user: no id returned.")
            user_id = result[0]  # internal DB id
            conn.commit()  # Commit the transaction
            return user_id
    finally:
        if close_conn:
            conn.close()


def upsert_artist(conn, artist_id: str, name: str, user_id: str, artist_image_url: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO artists (id, user_id, name, image_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id, user_id) DO NOTHING
            """,
            (artist_id, user_id, name, artist_image_url),
        )


def upsert_track(
    conn,
    track_id: str,
    user_id: str,
    name: str,
    artist_id: str,
    album_image_url: Optional[str],
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tracks (id, user_id, name, artist_id, album_image)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id, user_id) DO UPDATE
            SET album_image = EXCLUDED.album_image
            """,
            (track_id, user_id, name, artist_id, album_image_url),
        )


def insert_play(conn, user_id: str, track_id: str, played_at):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plays (user_id, track_id, played_at)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (user_id, track_id, played_at),
        )


# Functions for generate_report.py
def get_all_users(conn=None) -> list[dict]:
    """Return a list of all users from the database."""
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, spotify_user_id, display_name, email, refresh_token FROM users"
            )
            if cur.description is not None:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
            else:
                return []
    finally:
        if close_conn:
            conn.close()


def get_user_by_spotify_id(spotify_user_id: str, conn=None) -> Optional[dict]:
    """Get a specific user by their Spotify ID."""
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, spotify_user_id, display_name, email, refresh_token FROM users WHERE spotify_user_id = %s",
                (spotify_user_id,),
            )
            result = cur.fetchone()
            if result and cur.description:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, result))
            return None
    finally:
        if close_conn:
            conn.close()
