# 🛠️ Universal Data Diagnostic & Auto-Cleaning Pipeline

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Manipulation-150458.svg)](https://pandas.pydata.org/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com/)
[![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7.svg)](https://render.com/)

**Live Application:** [Click here to view the live app on Render](https://data-diagnostic-portfolio.onrender.com)

## 📖 Overview
As businesses ingest increasingly massive amounts of data, dirty datasets (missing values, extreme outliers, duplicates) bottleneck critical analytics. This project is a robust, interactive web application designed to automate the initial stages of the ETL (Extract, Transform, Load) pipeline. 

It allows non-technical stakeholders to upload raw CSV files, visually explore statistical anomalies, dynamically drop unneeded features, and download a mathematically cleaned, production-ready dataset in seconds. Under the hood, the app securely logs usage telemetry to a cloud PostgreSQL database.

## ✨ Key Features
* **Automated Data Cleaning Pipeline:** Dynamically handles missing values, drops exact duplicate rows, and mathematically caps extreme numeric outliers at the 1st and 99th percentiles.
* **Interactive EDA & Anomaly Detection:** Features a dynamic UI with Altair scatter charts that automatically detect and highlight statistical outliers (anomalies) in red before the data is cleaned.
* **Dynamic Feature Selection:** Users can interactively drop unnecessary columns prior to the cleaning execution.
* **Cloud Telemetry & Logging:** Securely and silently logs usage statistics (file size, rows, columns, missing values count) to a Supabase PostgreSQL database using environment variables and connection pooling.
* **Test-Driven Development (TDD):** Backed by a robust suite of 17 passing `pytest` unit tests ensuring the cleaning logic and database connection degrades gracefully.

## 🏗️ Technical Architecture
* **Frontend:** Streamlit, Altair (Data Visualization)
* **Backend Data Processing:** Python, Pandas, NumPy
* **Testing:** Pytest, Monkeypatch (Environment Mocking)
* **Cloud Database:** Supabase (PostgreSQL with Connection Pooling)
* **Deployment & CI/CD:** Render, GitHub

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/johari-Frias/data-diagnostic-portfolio.git](https://github.com/johari-Frias/data-diagnostic-portfolio.git)
   cd data-diagnostic-portfolio

2. **Install the dependencies:**

Bash
pip install -r requirements.txt

3. **Set up your environment variables:**

Create a .streamlit/secrets.toml file or a local .env file and add your Supabase connection string:

Ini, TOML
DATABASE_URL = "postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?sslmode=require"

4. Run the application:

Bash
streamlit run app.py

5. Run the test suite:

Bash
pytest tests/ -v


🧠 Business Value
This tool bridges the gap between raw data extraction and analytical modeling. By automating duplicate removal and outlier handling, it reduces the manual preprocessing time for Data Analysts from hours to seconds, ensuring downstream BI dashboards and machine learning models are fed with high-integrity data.


***

### The Final Push
Once you have pasted this into your `README.md` and added your live Render link, do your final push to GitHub:

```bash
git add README.md
git commit -m "docs: updated README with project architecture and live link"
git push origin main