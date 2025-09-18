# aggregator.py
from datetime import date, timedelta
from .db import get_conn


def load_weekly_data(user_id: int, week_start: date, week_end: date) -> dict:
    """Fetch tracks, artists, and user info from DB for a given week."""
    conn = get_conn()
    data = {"tracks": {}, "artists": {}, "user": None}
    try:
        with conn.cursor() as cur:
            # Top tracks
            cur.execute(
                """
                SELECT
                    t.id AS track_id,
                    t.name,
                    a.name AS artist_name,
                    a.id AS artist_id,
                    t.album_image,
                    COUNT(*) AS count
                FROM plays p
                JOIN tracks t ON p.track_id = t.id
                JOIN artists a ON t.artist_id = a.id
                WHERE p.user_id = %s AND p.played_at >= %s AND p.played_at < %s
                GROUP BY t.id, t.name, a.name, a.id, t.album_image
                """,
                (user_id, week_start, week_end),
            )
            for row in cur.fetchall():
                track_id, name, artist_name, artist_id, album_image, count = row
                data["tracks"][track_id] = {
                    "track_id": track_id,
                    "name": name,
                    "artist_name": artist_name,
                    "artist_id": artist_id,
                    "album_image": album_image,
                    "count": count,
                }

            # Top artists
            cur.execute(
                """
                SELECT
                    a.id AS artist_id,
                    a.name,
                    a.image_url,
                    COUNT(*) AS count
                FROM plays p
                JOIN tracks t ON p.track_id = t.id
                JOIN artists a ON t.artist_id = a.id
                WHERE p.user_id = %s AND p.played_at >= %s AND p.played_at < %s
                GROUP BY a.id, a.name, a.image_url
                """,
                (user_id, week_start, week_end),
            )
            for row in cur.fetchall():
                artist_id, name, artist_image, count = row
                data["artists"][artist_id] = {
                    "id": artist_id,
                    "name": name,
                    "artist_image": artist_image,
                    "count": count,
                }

            # User info
            cur.execute(
                "SELECT display_name, email FROM users WHERE id = %s", (user_id,)
            )
            row = cur.fetchone()
            if row:
                display_name, email = row
                data["user"] = {"display_name": display_name, "email": email}
            else:
                raise ValueError(f"User with ID {user_id} not found")

    finally:
        conn.close()

    return data


def get_week_range(today: date = date.today()):
    """Get start and end dates of the current week (Mon–Sun)."""
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    return week_start, week_end
