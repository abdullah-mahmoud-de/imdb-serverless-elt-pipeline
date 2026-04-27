# Orchestrating an IMDb ELT Pipeline: AWS to Snowflake Integration

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Snowflake](https://img.shields.io/badge/snowflake-%234285F4.svg?style=for-the-badge&logo=snowflake&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)

## 📌 Executive Summary
An automated, event-driven data pipeline that extracts daily IMDb metadata via AWS Lambda, merges it into a Snowflake data warehouse, and serves the clean data to a public Streamlit dashboard. 

### Key Highlights:
* **Automated AWS ELT Pipeline:** Built using EventBridge, Lambda, and SNS for reliable, scheduled IMDb data extraction directly into an S3 Data Lake.
* **Optimized Snowflake Ingestion:** Utilized Change Data Capture (CDC) and SQL `MERGE` operations, eliminating full-loads to achieve zero-downtime data availability.
* **Interactive Analytics:** Developed a public Streamlit dashboard powered by Snowflake, enabling live data visualization via SQL compute pushdown.

---

## 📊 Dataset
This project utilizes the official, publicly available **IMDb Non-Commercial Datasets**. 
* **Source:** [https://datasets.imdbws.com/](https://datasets.imdbws.com/)
* **Files Extracted:** `title.basics.tsv.gz` (core metadata) and `title.akas.tsv.gz` (regional data).

---

## 🏗️ Architecture Overview

The project is structured in a fully automated Modern Data Stack (MDS) workflow:
1. **Extraction (AWS Lambda):** Serverless function streams raw `.tsv.gz` metadata from IMDb APIs.
2. **Storage (Amazon S3):** Data lands in an S3 Data Lake bucket.
3. **Orchestration (AWS EventBridge & SNS):** Cron schedules automate the extraction, while SNS provides asynchronous email alerts upon failure.
4. **Data Warehousing & CDC (Snowflake):** Scheduled tasks ingest data from S3 to staging tables, merging changes into production tables.
5. **Transformation (Snowflake Views):** Dynamic SQL Views clean and aggregate data.
6. **Visualization (Streamlit):** An interactive frontend queries the transformed data in real-time.

---

## 📁 Repository Structure
```text
.
├── app.py                      # Main Streamlit dashboard application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── aws_scripts/
│   └── lambda_ingestion.py     # AWS Lambda extraction code
└── snowflake_scripts/
    ├── README.md               # Snowflake architecture documentation
    └── snowflake_setup.sql     # Complete DDL and Task setup script
```
---

## 🚀 How to Run Locally

Clone this repository: git clone https://github.com/abdullah-mahmoud-de/imdb-serverless-elt-pipeline.git

Install dependencies: `pip install -r requirements.txt`

Add your `secrets.toml` file to the `.streamlit/` directory with your Snowflake credentials.

Run the application: `streamlit run app.py`
