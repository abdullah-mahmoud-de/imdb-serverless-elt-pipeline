# Snowflake Data Warehouse Architecture

This directory contains the complete backend architecture for the IMDb ELT pipeline. 

The `snowflake_setup_complete.sql` file provides the top-to-bottom configuration required to build the cloud data warehouse, orchestrate external connections, secure the data, and automate the ingestion process.

## ⚙️ Architecture Breakdown

The SQL script is perfectly ordered for sequential execution and covers six critical domains:

1. **Infrastructure Setup:** * Provisions the `IMDB_DB` database, the `PUBLIC` schema, and an auto-suspending `COMPUTE_WH` virtual warehouse to optimize compute costs.
2. **S3 Integration:** * Configures the `STORAGE INTEGRATION` to securely connect Snowflake to the AWS S3 Data Lake using IAM roles.
   * Defines custom file formats to seamlessly unpack and read GZIP-compressed TSV files directly from the external stage.
3. **Table Schemas:** * Establishes the core data models, generating both transient `stg_` (Staging) tables for raw data drops and persistent production tables for titles and countries.
4. **Transformation View:** * Creates the `v_clean_movies` view. This acts as a dynamic transformation layer that filters adult content, normalizes runtime minutes, and prepares the data for frontend querying without duplicating storage.
5. **Security:** * Implements the Principle of Least Privilege by creating a dedicated `STREAMLIT_ROLE`.
   * Provisions a `streamlit_app_user` restricted exclusively to reading the specific transformation view required by the dashboard.
6. **Automated CDC (Change Data Capture):** * Deploys a fully scripted Snowflake `TASK` triggered by a Cron schedule.
   * Utilizes the `MERGE` (Upsert) command to compare staging data against production. It surgically updates existing records that have changed and inserts brand new records, completely eliminating the need for destructive daily full-loads and guaranteeing zero downtime for the Streamlit dashboard.

## 🚀 Execution Instructions
To deploy this architecture to your Snowflake instance:
1. Open a new SQL Worksheet in Snowsight.
2. Ensure you are operating under the `ACCOUNTADMIN` or `SYSADMIN` role.
3. Copy the contents of `snowflake_setup_complete.sql`, replace the placeholder AWS ARN and S3 Bucket paths with your specific AWS details, and execute the script.
