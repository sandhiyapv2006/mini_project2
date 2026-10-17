"""
Integration and Unit Test Suite for CineRate
Tests Flask endpoints, CSV loading/exporting, search, statistics, and scraper headless configuration.
"""

import os
import unittest
import json
import pandas as pd
from app import app, CSV_PATH, DATA_DIR
from imdb_scraper import get_headless_chrome_options, load_movies_from_csv, save_movies_to_csv


class CineRateTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_chrome_options_headless(self):
        """Verify that ChromeOptions includes headless mode and required flags."""
        options = get_headless_chrome_options()
        args = options.arguments
        self.assertIn("--headless=new", args, "Headless flag --headless=new missing")
        self.assertIn("--window-size=1920,1080", args, "Window size argument missing")
        self.assertIn("--disable-gpu", args, "GPU disable flag missing")

    def test_homepage_loads(self):
        """Verify that GET / returns status 200 and loads CineRate HTML."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CineRate", response.data)
        self.assertIn(b"Discover the World's Top Movies", response.data)

    def test_api_stats(self):
        """Verify GET /api/stats returns valid calculated metrics."""
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("total_movies", data)
        self.assertIn("average_rating", data)
        self.assertIn("highest_rated", data)
        if data["total_movies"] > 0:
            self.assertGreater(data["average_rating"], 0)

    def test_api_movies(self):
        """Verify GET /api/movies returns movies and supports sorting."""
        response = self.client.get("/api/movies?sort_by=rating&order=desc")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["movies"], list)
        if len(data["movies"]) >= 2:
            r1 = data["movies"][0]["IMDb Rating"] or 0
            r2 = data["movies"][1]["IMDb Rating"] or 0
            self.assertGreaterEqual(r1, r2)

    def test_api_search(self):
        """Verify GET /api/movies/search finds matching films."""
        # Search for Godfather
        response = self.client.get("/api/movies/search?q=godfather")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        for movie in data["movies"]:
            self.assertIn("godfather", movie["Movie Title"].lower())

    def test_api_search_missing_param(self):
        """Verify GET /api/movies/search returns 400 when query parameter is missing."""
        response = self.client.get("/api/movies/search?q=")
        self.assertEqual(response.status_code, 400)

    def test_api_export_csv(self):
        """Verify GET /api/export downloads CSV with correct header."""
        response = self.client.get("/api/export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"Rank,Movie Title,Release Year,IMDb Rating", response.data)

    def test_scrape_status_endpoint(self):
        """Verify GET /api/scrape/status returns valid JSON state."""
        response = self.client.get("/api/scrape/status")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("is_running", data)
        self.assertIn("status", data)


if __name__ == "__main__":
    unittest.main()
