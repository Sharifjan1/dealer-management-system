# Dealer Management System

Inventory and profit tracking for a used car dealership. Add a car by VIN, log what you spend on it (detail, tires, repairs, transport, auction fees), mark it sold, and see what each car made you.

![Backend tests](https://github.com/Sharifjan1/dealer-management-system/actions/workflows/backend-tests.yml/badge.svg)

## What it does

- Decodes a VIN through the NHTSA vehicle database to fill in year, make, model and trim
- Keeps the lot inventory with purchase price, asking price, miles and color
- Tracks costs per car and the total money in each one
- Shows profit at sticker price before a sale, and real profit and ROI after
- Gives a running total for the whole lot: money tied up, sales and profit

## Project layout

```
backend/            FastAPI app (Python)
  app/
    main.py         starts the API
    database.py     SQLite connection
    models.py       vehicles and expenses tables
    schemas.py      what the API accepts and returns
    routers/        API routes
    services/       money math and VIN decoding
  tests/            pytest tests
frontend/           the website (plain HTML, CSS and JavaScript)
.github/workflows/  runs the tests and publishes the website
```

## Run the backend

You need Python 3.10 or newer.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000. Open http://127.0.0.1:8000/docs to try every route in the browser.

## Run the tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

The tests also run on GitHub every time backend code is pushed. Check the Actions tab for results.

## Run the website

The live site is published from the `frontend` folder with GitHub Pages:
https://sharifjan1.github.io/dealer-management-system/

GitHub Pages only hosts the website files. It can't run the Python backend, so the site starts in demo mode with sample cars saved in your browser. To use real data:

1. Start the backend on your computer (see above).
2. On the site, switch from "Demo data" to "My API" and connect to `http://127.0.0.1:8000`.

Chrome may ask for permission to let the site reach your computer. Allow it.

You can also run the website locally:

```bash
cd frontend
python -m http.server 5500
```

Then open http://127.0.0.1:5500. When it runs locally it connects to your API by default.

## Tech

Python, FastAPI, SQLAlchemy, SQLite, pytest, HTML, CSS, JavaScript, GitHub Actions, GitHub Pages
