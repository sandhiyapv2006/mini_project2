# CineRate – IMDb Movie Rating Scraper & Discovery Web Platform

A full-stack, responsive web application that collects, processes, and displays top movie rankings, titles, release years, and IMDb ratings in an interactive modern interface.

Built with **Python Flask**, **Selenium WebDriver** (configured strictly with **Headless Chrome**), **Pandas**, and a modern **Dark Theme HTML5/CSS3/JavaScript** frontend.

---

## 🌟 Key Features

1. **Modern Dark Theme UI**:
   - Sleek dark background with Gold (`#f5c518`) and Orange accents inspired by IMDb.
   - Interactive hero banner with live statistics calculated directly from the movie dataset.
   - Fully responsive on desktop, tablet, and mobile devices.

2. **Headless Chrome Web Scraping (`imdb_scraper.py`)**:
   - Collects Movie Rank, Title, Release Year, and IMDb Rating.
   - Runs Selenium WebDriver in complete headless mode (`--headless=new`, `--window-size=1920,1080`, `--disable-gpu`).
   - **Zero visible Chrome pop-up windows** during background scraping jobs.
   - Asynchronous execution in Flask background threads — web browsing remains fast and unblocked.
   - Policy-compliant data fallback to authorized open movie repositories if IMDb bot protections/robots.txt restrict direct access.
   - Robust `finally` block to safely terminate WebDriver instances under all outcomes.

3. **Live Movie Search & Filters**:
   - Case-insensitive, partial-match title search.
   - Filtering by minimum IMDb rating (9.0+, 8.5+, 8.0+, etc.).
   - Multi-column sorting by Rank, IMDb Rating, Release Year, and Title.
   - Client-side pagination with selectable page sizes (10, 25, 50, 100).

4. **Real Dataset Statistics**:
   - Live calculations for Total Movies Collected, Average IMDb Rating, and Highest-Rated Movie.

5. **Instant CSV Export**:
   - One-click **Download CSV** button exporting verified data structured as `Rank`, `Movie Title`, `Release Year`, and `IMDb Rating`.

---

## 📁 Project Structure

```text
CineRate/
│
├── app.py                  # Flask web backend with REST APIs & background task manager
├── imdb_scraper.py         # Selenium headless Chrome scraper module & CSV handler
├── test_cinerate.py        # Automated test suite for APIs and scraper settings
├── requirements.txt        # Python package dependencies
├── README.md               # Complete project documentation
├── .gitignore              # Git ignore rules for Python, virtual environments & OS files
│
├── data/
│   ├── .gitkeep            # Ensures directory tracking
│   └── imdb_top250.csv     # Extracted movie dataset
│
├── templates/
│   └── index.html          # Frontend HTML5 template
│
└── static/
    ├── css/
    │   └── style.css       # Dark theme CSS styling & animations
    ├── js/
    │   └── script.js       # Asynchronous JavaScript (fetch API, sorting, search, polling)
    └── images/             # Static graphic assets
```

---

## 🛠️ Technologies Used

- **Frontend**: HTML5, CSS3 (Custom Dark Theme), Vanilla JavaScript (ES6+), Font Awesome 6.5.
- **Backend**: Python 3.10+, Flask 3.1.
- **Web Scraping & Automation**: Selenium WebDriver 4.x with Google Chrome Headless Mode.
- **Data Manipulation & Storage**: Pandas, CSV, Requests.

---

## 🚀 Installation & Setup Guide

### 1. Prerequisites
- **Python 3.10 or higher** installed.
- **Google Chrome** installed on your operating system.

### 2. Open Project in VS Code
Open your VS Code editor and navigate to the project directory:
```powershell
cd "c:\Users\Gopika S\Desktop\Mini Project_2"
```

### 3. Create a Virtual Environment (Recommended)
```powershell
python -m venv venv
```
Activate the virtual environment:
- On Windows PowerShell:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- On Command Prompt:
  ```cmd
  .\venv\Scripts\activate.bat
  ```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🎬 How to Run CineRate

### Start the Flask Server
Run the application using:
```powershell
python app.py
```
You will see output indicating the server has started:
```text
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

### Access in Chrome Browser
Open Google Chrome and navigate to:
```
http://127.0.0.1:5000
```

---

## 🤖 Headless Scraping Verification

To verify that the scraping process runs in **headless mode** without launching a visible browser window:

1. Open the website at `http://127.0.0.1:5000` in Google Chrome.
2. In the navbar or hero section, click the **"Refresh Movie Data"** button.
3. Observe that:
   - A gold status banner appears at the top: `Background scraping in progress (Headless Chrome)...`.
   - **No separate Google Chrome window opens on your desktop**.
   - Your website remains completely smooth and responsive.
   - When the scraping job completes, the status turns green, and the movie table and stats automatically refresh with updated data.

You can also run the scraper independently from the terminal:
```powershell
python imdb_scraper.py
```

---

## 🌐 REST API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the single-page web application |
| `GET` | `/api/movies` | Returns movie records with optional `min_rating`, `sort_by`, and `order` parameters |
| `GET` | `/api/movies/search?q=name` | Performs case-insensitive partial match search |
| `GET` | `/api/stats` | Returns computed summary metrics (`total_movies`, `average_rating`, `highest_rated`) |
| `GET` | `/api/export` | Generates and downloads the `cinerate_movies.csv` file |
| `POST`| `/api/scrape` | Dispatches an asynchronous background scraping task |
| `GET` | `/api/scrape/status` | Returns current scraping worker status and progress message |

---

## 🧪 Running Automated Tests

Run the included unit and integration test suite:
```powershell
python test_cinerate.py
```
This tests:
- Headless Chrome argument validation (`--headless=new`, `--disable-gpu`).
- Homepage rendering.
- Movie retrieval and sorting.
- Search API accuracy.
- CSV export streaming.
- Scraping status endpoint responses.

---

## ⚖️ Data Source Notice & Compliance

CineRate respects website terms of service and robots policies. Direct scraping against IMDb may be subject to Amazon AWS WAF, CAPTCHAs, or rate-limiting. CineRate includes a compliant fallback pipeline to verified open movie repositories, parsing real IMDb-rated movie entities through Selenium headless Chrome into `data/imdb_top250.csv`.
