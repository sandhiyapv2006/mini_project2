"""
CineRate - Flask Web Application Backend
=========================================
Provides REST API endpoints and template routing for CineRate:
- GET /                    : Serves the frontend single page app
- GET /api/movies          : Returns paginated/filtered/sorted movie records
- GET /api/movies/search   : Case-insensitive search on movie titles
- GET /api/stats           : Statistics calculated from current CSV dataset
- GET /api/export          : CSV export endpoint
- POST /api/scrape         : Triggers background scraping worker
- GET /api/scrape/status   : Polls background scraping status
"""

import os
import threading
import logging
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, Response
import pandas as pd
from imdb_scraper import (
    load_movies_from_csv,
    run_scraping_job,
    CSV_PATH,
    DATA_DIR
)

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CineRateApp")

# Background job tracking state
scrape_lock = threading.Lock()
scrape_state = {
    "is_running": False,
    "progress": "",
    "status": "idle",  # 'idle', 'running', 'success', 'error'
    "message": "Ready to scrape movie records.",
    "count": 0,
    "elapsed_seconds": 0
}


def background_scraper_task():
    """Background worker that calls the scraper and updates global state."""
    global scrape_state
    def progress_callback(msg):
        with scrape_lock:
            scrape_state["progress"] = msg

    try:
        result = run_scraping_job(progress_callback=progress_callback)
        with scrape_lock:
            scrape_state["is_running"] = False
            scrape_state["status"] = result.get("status", "success")
            scrape_state["message"] = result.get("message", "Scraping completed.")
            scrape_state["count"] = result.get("count", 0)
            scrape_state["elapsed_seconds"] = result.get("elapsed_seconds", 0)
    except Exception as exc:
        logger.error(f"Background scraping thread crashed: {exc}")
        with scrape_lock:
            scrape_state["is_running"] = False
            scrape_state["status"] = "error"
            scrape_state["message"] = f"Scraping process encountered an error: {str(exc)}"


# ------------------ Routes ------------------ #

@app.route("/")
def index():
    """Serves the CineRate homepage."""
    return render_template("index.html")


@app.route("/api/movies", methods=["GET"])
def get_movies():
    """
    Returns available movie records with sorting and rating filtering.
    Query parameters:
    - min_rating (float): optional filter for IMDb rating >= min_rating
    - sort_by (str): 'rank', 'year', 'rating', 'title' (default: 'rank')
    - order (str): 'asc' or 'desc' (default: 'asc')
    """
    try:
        movies = load_movies_from_csv(CSV_PATH)
        if not movies:
            return jsonify({
                "success": True,
                "count": 0,
                "movies": [],
                "message": "No movie data available yet. Click 'Refresh Movie Data' to run scraper."
            }), 200

        # Filter by minimum rating
        min_rating_arg = request.args.get("min_rating", type=float)
        if min_rating_arg is not None:
            movies = [m for m in movies if m.get("IMDb Rating") is not None and m["IMDb Rating"] >= min_rating_arg]

        # Sorting
        sort_by = request.args.get("sort_by", "rank").lower()
        order = request.args.get("order", "asc").lower()
        reverse = (order == "desc")

        if sort_by == "rank":
            movies.sort(key=lambda x: (x.get("Rank") is None, x.get("Rank", 9999)), reverse=reverse)
        elif sort_by == "year":
            movies.sort(key=lambda x: (x.get("Release Year") is None, x.get("Release Year", 0)), reverse=reverse)
        elif sort_by == "rating":
            movies.sort(key=lambda x: (x.get("IMDb Rating") is None, x.get("IMDb Rating", 0.0)), reverse=reverse)
        elif sort_by == "title":
            movies.sort(key=lambda x: x.get("Movie Title", "").lower(), reverse=reverse)

        return jsonify({
            "success": True,
            "count": len(movies),
            "movies": movies
        }), 200

    except Exception as e:
        logger.error(f"Error in /api/movies: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve movies data."
        }), 500


@app.route("/api/movies/search", methods=["GET"])
def search_movies():
    """
    Search available movie records by partial, case-insensitive title.
    Query parameter:
    - q (str): search term
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({
            "success": False,
            "error": "Search query parameter 'q' is required."
        }), 400

    try:
        movies = load_movies_from_csv(CSV_PATH)
        if not movies:
            return jsonify({
                "success": True,
                "query": query,
                "count": 0,
                "movies": [],
                "message": "No movie dataset available to search. Please scrape first."
            }), 200

        query_lower = query.lower()
        results = [m for m in movies if query_lower in m.get("Movie Title", "").lower()]

        return jsonify({
            "success": True,
            "query": query,
            "count": len(results),
            "movies": results
        }), 200

    except Exception as e:
        logger.error(f"Error in /api/movies/search: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred while searching movies."
        }), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Returns actual calculated statistics from available movie records:
    - total_movies: count of records
    - average_rating: mean IMDb rating (formatted to 2 decimal places)
    - highest_rated: top movie details
    - lowest_rated: lowest rated movie in top records
    """
    try:
        movies = load_movies_from_csv(CSV_PATH)
        if not movies:
            return jsonify({
                "success": True,
                "total_movies": 0,
                "average_rating": 0.0,
                "highest_rated": None,
                "lowest_rated": None,
                "message": "Dataset empty. Please scrape movie data."
            }), 200

        ratings = [m["IMDb Rating"] for m in movies if m.get("IMDb Rating") is not None]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

        # Sort to find highest and lowest
        valid_rated = [m for m in movies if m.get("IMDb Rating") is not None]
        highest_movie = max(valid_rated, key=lambda x: x["IMDb Rating"]) if valid_rated else None
        lowest_movie = min(valid_rated, key=lambda x: x["IMDb Rating"]) if valid_rated else None

        return jsonify({
            "success": True,
            "total_movies": len(movies),
            "average_rating": avg_rating,
            "highest_rated": highest_movie,
            "lowest_rated": lowest_movie
        }), 200

    except Exception as e:
        logger.error(f"Error in /api/stats: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to calculate movie statistics."
        }), 500


@app.route("/api/export", methods=["GET"])
def export_csv():
    """
    Exports available movie records as a downloadable CSV file.
    Uses Pandas to structure the export.
    Returns 404/400 if dataset is empty.
    """
    try:
        if not os.path.exists(CSV_PATH):
            return jsonify({
                "success": False,
                "error": "No movie data has been collected yet. Please run the scraper first."
            }), 404

        df = pd.read_csv(CSV_PATH, encoding="utf-8")
        if df.empty:
            return jsonify({
                "success": False,
                "error": "The movie dataset is empty. Nothing to export."
            }), 400

        # Re-ensure standard columns
        cols = ["Rank", "Movie Title", "Release Year", "IMDb Rating"]
        for c in cols:
            if c not in df.columns:
                df[c] = None
        df = df[cols]

        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_buffer.seek(0)

        return send_file(
            csv_buffer,
            mimetype="text/csv",
            as_attachment=True,
            download_name="cinerate_movies.csv"
        )

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate CSV export file."
        }), 500


@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    """
    Starts an asynchronous background scraping job using headless Chrome.
    Prevents duplicate simultaneous jobs.
    """
    global scrape_state
    with scrape_lock:
        if scrape_state["is_running"]:
            return jsonify({
                "success": False,
                "message": "A movie scraping job is already actively running in the background. Please wait."
            }), 409

        scrape_state["is_running"] = True
        scrape_state["status"] = "running"
        scrape_state["progress"] = "Starting headless Chrome..."
        scrape_state["message"] = "Data collection initiated."

    thread = threading.Thread(target=background_scraper_task, daemon=True)
    thread.start()

    return jsonify({
        "success": True,
        "message": "Movie scraping job started in background using headless Chrome. Monitor status via /api/scrape/status."
    }), 202


@app.route("/api/scrape/status", methods=["GET"])
def scrape_status():
    """Returns the current background scraping job status and progress."""
    with scrape_lock:
        return jsonify({
            "success": True,
            "is_running": scrape_state["is_running"],
            "status": scrape_state["status"],
            "progress": scrape_state["progress"],
            "message": scrape_state["message"],
            "count": scrape_state["count"],
            "elapsed_seconds": scrape_state["elapsed_seconds"]
        }), 200


if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info("Starting CineRate server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
