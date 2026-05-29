from __future__ import annotations

import contextlib
import html
import io
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent
NOTEBOOK_PATH = APP_DIR / "Main_Model.ipynb"
REQUIRED_DATASETS = ["tmdb_5000_movies.csv", "tmdb_5000_credits.csv"]
TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

load_dotenv(APP_DIR / ".env")


st.set_page_config(
    page_title="CineMatch AI",
    page_icon="CM",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    """Apply the cinematic dark visual system used across the app."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

            :root {
                --bg: #08090f;
                --panel: rgba(18, 21, 34, 0.78);
                --panel-strong: rgba(25, 29, 46, 0.92);
                --text: #f7f7fb;
                --muted: #a7adbd;
                --accent: #e50914;
                --gold: #f6c85f;
                --line: rgba(255, 255, 255, 0.10);
            }

            html, body, [class*="css"] {
                font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            }

            .stApp {
                color: var(--text);
                background:
                    radial-gradient(circle at 18% 10%, rgba(229, 9, 20, 0.24), transparent 30%),
                    radial-gradient(circle at 82% 0%, rgba(246, 200, 95, 0.14), transparent 25%),
                    linear-gradient(145deg, #07080d 0%, #101321 48%, #08090f 100%);
            }

            [data-testid="stSidebar"] {
                background: rgba(7, 8, 13, 0.92);
                border-right: 1px solid var(--line);
            }

            [data-testid="stSidebar"] * {
                color: var(--text);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1280px;
            }

            .hero {
                min-height: 290px;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                padding: 42px;
                border: 1px solid var(--line);
                border-radius: 8px;
                overflow: hidden;
                background:
                    linear-gradient(90deg, rgba(8, 9, 15, 0.96) 0%, rgba(8, 9, 15, 0.72) 46%, rgba(8, 9, 15, 0.20) 100%),
                    url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1800&q=80');
                background-size: cover;
                background-position: center;
                box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
            }

            .eyebrow {
                color: var(--gold);
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                margin-bottom: 0.85rem;
            }

            .hero h1 {
                max-width: 760px;
                font-size: clamp(2.4rem, 6vw, 5.4rem);
                line-height: 0.95;
                letter-spacing: 0;
                margin: 0;
            }

            .hero p {
                max-width: 660px;
                color: #d8dbe6;
                font-size: 1.05rem;
                line-height: 1.7;
                margin: 1.1rem 0 0;
            }

            .metric-strip {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 14px;
                margin: 18px 0 30px;
            }

            .metric {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 18px 20px;
                backdrop-filter: blur(18px);
            }

            .metric strong {
                display: block;
                font-size: 1.45rem;
                margin-bottom: 4px;
            }

            .metric span {
                color: var(--muted);
                font-size: 0.88rem;
            }

            .section-title {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 18px;
                margin-top: 10px;
                margin-bottom: 14px;
            }

            .section-title h2 {
                font-size: 1.35rem;
                margin: 0;
            }

            .section-title span {
                color: var(--muted);
                font-size: 0.92rem;
            }

            div[data-testid="stSelectbox"] > div,
            div[data-testid="stTextInput"] > div {
                background: rgba(255, 255, 255, 0.06);
                border-radius: 8px;
            }

            .stButton > button {
                width: 100%;
                min-height: 46px;
                border: 0;
                border-radius: 8px;
                color: white;
                font-weight: 800;
                background: linear-gradient(135deg, #e50914 0%, #b20710 100%);
                box-shadow: 0 16px 32px rgba(229, 9, 20, 0.24);
                transition: transform 160ms ease, box-shadow 160ms ease;
            }

            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 20px 40px rgba(229, 9, 20, 0.34);
            }

            .movie-card {
                position: relative;
                min-height: 420px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background:
                    linear-gradient(180deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 42%, rgba(0, 0, 0, 0.65) 100%),
                    linear-gradient(135deg, #2b314b 0%, #101321 48%, #29090d 100%);
                overflow: hidden;
                box-shadow: 0 18px 44px rgba(0, 0, 0, 0.38);
                transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
            }

            .movie-card.with-poster {
                background: #111521;
            }

            .movie-card:hover {
                transform: translateY(-6px);
                border-color: rgba(229, 9, 20, 0.55);
                box-shadow: 0 26px 58px rgba(0, 0, 0, 0.48);
            }

            .poster-img {
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
                object-fit: cover;
                transform: scale(1.01);
                transition: transform 220ms ease, filter 220ms ease;
            }

            .movie-card:hover .poster-img {
                transform: scale(1.06);
                filter: saturate(1.12) contrast(1.05);
            }

            .movie-card::after {
                content: "";
                position: absolute;
                inset: 0;
                background:
                    linear-gradient(180deg, rgba(0, 0, 0, 0.08) 0%, rgba(0, 0, 0, 0.08) 40%, rgba(0, 0, 0, 0.88) 100%),
                    linear-gradient(90deg, rgba(0, 0, 0, 0.50) 0%, transparent 45%);
                pointer-events: none;
            }

            .rank {
                position: relative;
                z-index: 2;
                width: 42px;
                height: 42px;
                display: grid;
                place-items: center;
                border-radius: 50%;
                color: white;
                font-weight: 900;
                background: rgba(229, 9, 20, 0.92);
                box-shadow: 0 12px 26px rgba(229, 9, 20, 0.28);
            }

            .poster-mark {
                position: absolute;
                right: -10px;
                top: 36px;
                color: rgba(255, 255, 255, 0.055);
                font-size: 8.4rem;
                font-weight: 900;
                line-height: 1;
                z-index: 1;
            }

            .movie-meta {
                position: absolute;
                left: 18px;
                right: 18px;
                bottom: 18px;
                z-index: 2;
            }

            .movie-card h3 {
                font-size: 1.25rem;
                line-height: 1.25;
                margin: 0 0 12px;
            }

            .chips {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .chip {
                display: inline-flex;
                align-items: center;
                min-height: 28px;
                padding: 0 10px;
                border-radius: 999px;
                color: #f0f2f8;
                background: rgba(255, 255, 255, 0.09);
                border: 1px solid rgba(255, 255, 255, 0.10);
                font-size: 0.78rem;
                font-weight: 700;
            }

            .empty-state {
                padding: 26px;
                border-radius: 8px;
                border: 1px dashed rgba(255, 255, 255, 0.18);
                background: rgba(255, 255, 255, 0.05);
                color: var(--muted);
            }

            .poster-note {
                color: var(--muted);
                font-size: 0.86rem;
                margin: -6px 0 18px;
            }

            @media (max-width: 760px) {
                .hero {
                    min-height: 360px;
                    padding: 28px;
                }

                .metric-strip {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _execute_notebook_model() -> tuple[pd.DataFrame, Any, dict[str, Any], pd.DataFrame]:
    """Execute the existing notebook cells and return its trained artifacts.

    The recommendation function and similarity matrix come directly from
    Main_Model.ipynb. The notebook file itself is never edited.
    """
    if not NOTEBOOK_PATH.exists():
        raise FileNotFoundError("Main_Model.ipynb was not found beside app.py.")

    with NOTEBOOK_PATH.open("r", encoding="utf-8") as file:
        notebook = json.load(file)

    namespace: dict[str, Any] = {"__name__": "__streamlit_notebook_loader__"}
    display_catalog = pd.DataFrame()
    previous_cwd = Path.cwd()
    os.chdir(APP_DIR)

    try:
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") != "code":
                continue

            source = "".join(cell.get("source", []))
            stripped = source.strip()

            # UI integration loads the trained notebook state but skips demo
            # execution and pickle export side effects.
            if not stripped or stripped.startswith("recommend(") or "pickle.dump" in stripped:
                continue

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                exec(compile(source, str(NOTEBOOK_PATH), "exec"), namespace)

            if "movies" in namespace and {"title", "id"}.issubset(namespace["movies"].columns):
                current_movies = namespace["movies"]
                metadata_columns = [
                    column
                    for column in ["id", "title", "release_date", "vote_average", "vote_count", "popularity"]
                    if column in current_movies.columns
                ]
                if {"release_date", "vote_average"}.issubset(current_movies.columns):
                    display_catalog = current_movies[metadata_columns].copy()
    finally:
        os.chdir(previous_cwd)

    if "new_df" not in namespace or "similarity" not in namespace or "recommend" not in namespace:
        raise RuntimeError("The notebook did not produce new_df, similarity, and recommend().")

    return namespace["new_df"], namespace["similarity"], namespace, display_catalog


@st.cache_resource(show_spinner=False)
def load_recommender() -> tuple[pd.DataFrame, Any, dict[str, Any], pd.DataFrame]:
    """Cache notebook execution so the app stays fast after first load."""
    return _execute_notebook_model()


def missing_dataset_files() -> list[str]:
    """Return notebook input files that are required but not present locally."""
    return [filename for filename in REQUIRED_DATASETS if not (APP_DIR / filename).exists()]


def get_tmdb_api_key() -> str:
    """Read a TMDB API key from Streamlit secrets or the local environment."""
    with contextlib.suppress(Exception):
        secret_key = st.secrets.get("TMDB_API_KEY")
        if secret_key:
            return str(secret_key)
    return os.getenv("TMDB_API_KEY", "").strip()


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def fetch_poster_url(title: str, tmdb_id: Any, year: Any, api_key: str) -> str | None:
    """Fetch a poster from TMDB and cache the result for a day."""
    if not api_key:
        return None

    try:
        numeric_id = int(tmdb_id)
    except (TypeError, ValueError):
        numeric_id = None

    try:
        if numeric_id:
            response = requests.get(
                f"{TMDB_API_BASE}/movie/{numeric_id}",
                params={"api_key": api_key, "language": "en-US"},
                timeout=6,
            )
            if response.ok:
                poster_path = response.json().get("poster_path")
                if poster_path:
                    return f"{TMDB_IMAGE_BASE}{poster_path}"

        search_params: dict[str, Any] = {
            "api_key": api_key,
            "query": title,
            "language": "en-US",
            "include_adult": "false",
        }
        if pd.notna(year):
            search_params["year"] = int(year)

        response = requests.get(f"{TMDB_API_BASE}/search/movie", params=search_params, timeout=6)
        if not response.ok:
            return None

        results = response.json().get("results", [])
        for result in results:
            poster_path = result.get("poster_path")
            if poster_path:
                return f"{TMDB_IMAGE_BASE}{poster_path}"
    except requests.RequestException:
        return None

    return None


def resolve_movie_title(query: str, titles: list[str]) -> str | None:
    """Resolve exact or case-insensitive UI input to a notebook movie title."""
    query = query.strip()
    if not query:
        return None
    if query in titles:
        return query

    lowered = {title.lower(): title for title in titles}
    return lowered.get(query.lower())


def recommendations_from_notebook(movie: str, namespace: dict[str, Any], catalog: pd.DataFrame) -> pd.DataFrame:
    """Call the notebook's recommend(movie) function and shape its printed output for the UI."""
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        namespace["recommend"](movie)

    titles = [line.strip() for line in output.getvalue().splitlines() if line.strip()]
    if not titles:
        return pd.DataFrame(columns=["title", "id", "year", "rating"])

    new_df = namespace["new_df"]
    rows = new_df[new_df["title"].isin(titles)][["id", "title"]].copy()
    rows["title"] = pd.Categorical(rows["title"], categories=titles, ordered=True)
    rows = rows.sort_values("title").reset_index(drop=True)
    rows["title"] = rows["title"].astype(str)

    if not catalog.empty:
        rows = rows.merge(catalog.drop_duplicates("title"), on=["id", "title"], how="left")

    rows["year"] = pd.to_datetime(rows.get("release_date"), errors="coerce").dt.year if "release_date" in rows else None
    rows["rating"] = rows["vote_average"].round(1) if "vote_average" in rows else None
    return rows


def render_metric_strip(movie_count: int, vector_count: int) -> None:
    st.markdown(
        f"""
        <div class="metric-strip">
            <div class="metric"><strong>{movie_count:,}</strong><span>movies in the trained catalogue</span></div>
            <div class="metric"><strong>{vector_count:,}</strong><span>text features from the notebook model</span></div>
            <div class="metric"><strong>5</strong><span>recommendations per search</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Portfolio Showcase</div>
            <h1>Cinematic Movie Recommendations</h1>
            <p>
                A polished Streamlit experience wrapped around your existing notebook-trained
                content-based recommender.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_movie_card(row: pd.Series, rank: int) -> None:
    title = str(row.get("title", "Untitled"))
    safe_title = html.escape(title)
    year = row.get("year")
    rating = row.get("rating")
    movie_id = row.get("id")
    initial = "".join(part[0] for part in title.split()[:2]).upper()[:2]
    poster_url = row.get("poster_url")
    safe_poster_url = html.escape(str(poster_url), quote=True) if poster_url else ""

    year_chip = f"<span class='chip'>{int(year)}</span>" if pd.notna(year) else ""
    rating_chip = f"<span class='chip'>Rating {rating:.1f}</span>" if pd.notna(rating) else ""
    id_chip = f"<span class='chip'>TMDB {movie_id}</span>" if pd.notna(movie_id) else ""
    poster_img = f"<img class='poster-img' src='{safe_poster_url}' alt='{safe_title} poster' loading='lazy'>" if poster_url else ""
    fallback_mark = "" if poster_url else f"<div class='poster-mark'>{initial}</div>"
    card_class = "movie-card with-poster" if poster_url else "movie-card"

    card_html = (
        f'<div class="{card_class}">'
        f"{poster_img}"
        f'<div class="rank">{rank}</div>'
        f"{fallback_mark}"
        '<div class="movie-meta">'
        f"<h3>{safe_title}</h3>"
        '<div class="chips">'
        f"{year_chip}{rating_chip}{id_chip}"
        "</div>"
        "</div>"
        "</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)


def main() -> None:
    inject_css()

    st.sidebar.markdown("## CineMatch AI")
    st.sidebar.caption("Notebook-powered movie recommendations")
    render_hero()

    missing_files = missing_dataset_files()
    if missing_files:
        st.error("The Streamlit frontend is ready, but the notebook dataset files are missing.")
        st.info(
            "Place these files in the project folder beside `Main_Model.ipynb`: "
            + ", ".join(f"`{filename}`" for filename in missing_files)
        )
        st.stop()

    try:
        with st.spinner("Loading the trained notebook model..."):
            new_df, similarity, namespace, catalog = load_recommender()
    except FileNotFoundError as exc:
        st.error(f"Required notebook file not found: {exc}")
        st.stop()
    except Exception as exc:
        st.error("The Streamlit UI could not load the trained notebook model.")
        st.info(
            "Make sure `tmdb_5000_movies.csv` and `tmdb_5000_credits.csv` are in the same folder as "
            "`Main_Model.ipynb`, then refresh the app."
        )
        st.exception(exc)
        st.stop()

    titles = sorted(new_df["title"].dropna().astype(str).unique().tolist())
    default_movie = "Spectre" if "Spectre" in titles else titles[0]

    selected = st.sidebar.selectbox("Choose a movie", titles, index=titles.index(default_movie))
    typed = st.sidebar.text_input("Or type a movie title", placeholder="Example: Avatar")
    st.sidebar.markdown("---")
    st.sidebar.caption("Poster source")
    if get_tmdb_api_key():
        st.sidebar.success("TMDB posters enabled")
    else:
        st.sidebar.info("Set TMDB_API_KEY to enable live posters")
    st.sidebar.markdown("---")
    st.sidebar.caption("Model source")
    st.sidebar.code("Main_Model.ipynb", language="text")

    render_metric_strip(len(titles), similarity.shape[1] if hasattr(similarity, "shape") else 0)

    movie_query = typed.strip() or selected
    resolved_movie = resolve_movie_title(movie_query, titles)

    left, right = st.columns([0.74, 0.26], vertical_alignment="bottom")
    with left:
        safe_selected_title = html.escape(str(resolved_movie or movie_query))
        st.markdown(
            f"""
            <div class="section-title">
                <h2>Recommendation Board</h2>
                <span>Selected title: {safe_selected_title}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        find_button = st.button("Find Similar Movies", type="primary")

    if resolved_movie is None:
        st.markdown(
            """
            <div class="empty-state">
                No exact title was found in the notebook catalogue. Try selecting a movie from the sidebar.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if find_button or resolved_movie:
        with st.spinner("Finding the closest matches from the notebook model..."):
            recommendations = recommendations_from_notebook(resolved_movie, namespace, catalog)

        if recommendations.empty:
            st.markdown(
                """
                <div class="empty-state">
                    The notebook returned no recommendations for this title.
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        api_key = get_tmdb_api_key()
        if api_key:
            with st.spinner("Loading movie posters..."):
                recommendations["poster_url"] = recommendations.apply(
                    lambda row: fetch_poster_url(row["title"], row.get("id"), row.get("year"), api_key),
                    axis=1,
                )
        else:
            recommendations["poster_url"] = None
            st.markdown(
                """
                <div class="poster-note">
                    Add a TMDB_API_KEY environment variable to show live poster artwork on every card.
                </div>
                """,
                unsafe_allow_html=True,
            )

        columns = st.columns(5)
        for index, row in recommendations.iterrows():
            with columns[index % 5]:
                render_movie_card(row, index + 1)


if __name__ == "__main__":
    main()
