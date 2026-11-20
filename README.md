# Job Market Analysis & Recommendation Dashboard

A Streamlit dashboard for exploring job listings and finding posts whose titles match a search query. This project includes the analysis notebook and a lightweight interactive dashboard by **Ankita Mohanty**.

## Features

- Analyze job-title keyword pay patterns, posting trends, and country comparisons in `Job_Market_Analysis.ipynb`
- Search hourly or fixed-price listings by job-title keywords
- Choose how many matching listings to display
- Browse listing details and open the original post
- Explore quick statistics for an uploaded dataset

## Data

The raw dataset is not included in this repository. Download the project CSV (`all_upwork_jobs_2024-02-07-2024-03-24.csv`) from its original source and place it beside `app.py` and `Job_Market_Analysis.ipynb`, or upload it through the dashboard. The app expects `title`, `is_hourly`, `hourly_low`, `hourly_high`, `budget`, and `country`; it uses `published_date` and `link` when available. CSV files are excluded by `.gitignore`.

## Run the dashboard locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```bash
   python -m streamlit run app.py
   ```

5. Upload the CSV in the app, or place it beside `app.py` before starting the app.

On Windows, `run_dashboard.bat` can start the app after dependencies are installed.

## Run the analysis notebook

Open `Job_Market_Analysis.ipynb` in Jupyter or VS Code after placing the CSV beside the notebook. Install the requirements first so pandas and matplotlib are available.

## Run with Docker

```bash
docker compose up --build
```

Then open <http://localhost:8501> and upload the CSV in the dashboard.

## Analysis notes and limitations

The recommendation prototype matches words in job titles; it is not a trained personalization model. The dataset does not include job descriptions, skills, or an explicit remote-work field, so recommendations and remote-work conclusions are limited by the available columns. Currency is unspecified. Hourly-rate comparisons are descriptive, and any treatment of the dataset's upper-rate value of 999 should be documented as an assumption unless verified against the source.
