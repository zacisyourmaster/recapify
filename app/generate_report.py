from .aggregator import load_weekly_data
from datetime import timedelta


from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import date
import os


OUTPUT_DIR = "reports"
TEMPLATE_DIR = "templates"
TEMPLATE_NAME = "weekly_report.html"
# Place new function after TEMPLATE_NAME definition


def generate_user_weekly_report(
    user_id, year, week, top_n=5, template_name=TEMPLATE_NAME
):
    """
    Generate HTML report for a specific user and week.
    """
    # Calculate week start/end
    week_start = date.fromisocalendar(year, week, 1)
    week_end = week_start + timedelta(days=7)
    data = load_weekly_data(user_id, week_start, week_end)
    # Use the last day of the ISO week as the "today" display for that report
    display_date = week_end - timedelta(days=1)
    return generate_html_report(
        data,
        top_n=top_n,
        template_name=template_name,
        year=year,
        week=week,
        today=display_date,
    )


def make_spotify_track_url(track_id):
    return f"https://open.spotify.com/track/{track_id}"


def make_spotify_artist_url(artist_id):
    return f"https://open.spotify.com/artist/{artist_id}"


def top_n_sorted(dict_values, n=5, key="count"):
    """
    Accepts an iterable of dict entries (values of tracks/artists)
    and returns top n sorted by `key` descending.
    """
    return sorted(dict_values, key=lambda x: x.get(key, 0), reverse=True)[:n]


def setup_jinja_env(template_dir=TEMPLATE_DIR):
    """Set up Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Add custom filters
    env.filters["spotify_track_url"] = make_spotify_track_url
    env.filters["spotify_artist_url"] = make_spotify_artist_url

    return env


def generate_html_report(
    data: dict,
    top_n=5,
    template_name=TEMPLATE_NAME,
    year: int | None = None,
    week: int | None = None,
    today: date | None = None,
):
    # Allow callers to override the reporting period, else default to current week
    if today is None:
        today = date.today()
    if year is None or week is None:
        year, week, _ = today.isocalendar()

    env = setup_jinja_env()
    template = env.get_template(template_name)

    html = template.render(
        user_display_name=data["user"]["display_name"],
        year=year,
        week=week,
        today=today,
        top_tracks=top_n_sorted(list(data["tracks"].values()), top_n),
        top_artists=top_n_sorted(list(data["artists"].values()), top_n),
        all_tracks=sorted(
            data["tracks"].values(), key=lambda x: x["count"], reverse=True
        ),
        all_artists=sorted(
            data["artists"].values(), key=lambda x: x["count"], reverse=True
        ),
        has_tracks=bool(data["tracks"]),
        has_artists=bool(data["artists"]),
    )
    return html


def write_report_file(html, out_dir=OUTPUT_DIR):
    today = date.today()
    year, week, _ = today.isocalendar()
    os.makedirs(out_dir, exist_ok=True)
    filename = f"weekly_report_{year}_w{week}.html"
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def ensure_template_dir_exists(template_dir=TEMPLATE_DIR):
    """Ensure template directory exists."""
    if not os.path.exists(template_dir):
        os.makedirs(template_dir, exist_ok=True)
        print(f"Created template directory: {template_dir}")
        print(
            f"Please create the template file: {os.path.join(template_dir, TEMPLATE_NAME)}"
        )
        return False

    template_path = os.path.join(template_dir, TEMPLATE_NAME)
    if not os.path.exists(template_path):
        print(f"Template file not found: {template_path}")
        print("Please create the template file.")
        return False

    return True
