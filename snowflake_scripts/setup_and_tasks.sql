-- ==============================================================================
-- IMDb Data Engineering Pipeline - Complete Snowflake Setup
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. DATABASE & WAREHOUSE SETUP
-- ------------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS IMDB_DB;
USE DATABASE IMDB_DB;

CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;

CREATE OR REPLACE WAREHOUSE COMPUTE_WH 
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 60 
AUTO_RESUME = TRUE;


-- ------------------------------------------------------------------------------
-- 2. EXTERNAL STAGE SETUP (Connect to S3)
-- ------------------------------------------------------------------------------
-- Note: Replace with your actual AWS IAM Role ARN and S3 bucket URI
CREATE OR REPLACE STORAGE INTEGRATION s3_imdb_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/YOUR_SNOWFLAKE_ROLE'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-s3-bucket-name/');

DESCRIBE INTEGRATION s3_imdb_integration;

-- Create File Format for compressed TSV files
CREATE OR REPLACE FILE FORMAT tsv_gz_format
  TYPE = CSV
  COMPRESSION = GZIP
  FIELD_DELIMITER = '\t'
  SKIP_HEADER = 1
  NULL_IF = ('\\N', 'NULL', '')
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- Create the Stage
CREATE OR REPLACE STAGE my_s3_imdb_stage
  STORAGE_INTEGRATION = s3_imdb_integration
  URL = 's3://your-s3-bucket-name/'
  FILE_FORMAT = tsv_gz_format;

LIST @my_s3_imdb_stage;

-- ------------------------------------------------------------------------------
-- 3. PRODUCTION & STAGING TABLES
-- ------------------------------------------------------------------------------
-- Staging Table for Titles
CREATE OR REPLACE TABLE stg_imdb_titles (
    tconst VARCHAR,          
    titleType VARCHAR,       
    primaryTitle VARCHAR,    
    originalTitle VARCHAR,   
    isAdult BOOLEAN,         
    startYear INT,           
    endYear INT,             
    runtimeMinutes INT,      
    genres VARCHAR           
);

-- Production Table for Titles
CREATE OR REPLACE TABLE imdb_titles CLONE stg_imdb_titles;

-- Staging Table for Countries
CREATE OR REPLACE TABLE stg_imdb_countries (
    titleId VARCHAR,         
    ordering INT,            
    title VARCHAR,           
    region VARCHAR,          
    language VARCHAR,        
    types VARCHAR,           
    attributes VARCHAR,      
    isOriginalTitle BOOLEAN  
);

-- Production Table for Countries
CREATE OR REPLACE TABLE imdb_countries CLONE stg_imdb_countries;


-- ------------------------------------------------------------------------------
-- 4. DATA TRANSFORMATION VIEW (For Streamlit)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_clean_movies AS
SELECT 
    t.primaryTitle AS title,
    t.startYear AS release_year,
    t.runtimeMinutes AS runtime_mins,
    t.genres,
    LISTAGG(DISTINCT c.region, ', ') AS available_regions
FROM imdb_titles t
LEFT JOIN imdb_countries c ON t.tconst = c.titleId
WHERE t.titleType = 'movie' 
  AND t.isAdult = FALSE
GROUP BY 1, 2, 3, 4;


-- ------------------------------------------------------------------------------
-- 5. STREAMLIT USER & SECURITY
-- ------------------------------------------------------------------------------
-- Create a read-only role for the Streamlit dashboard
CREATE ROLE IF NOT EXISTS STREAMLIT_ROLE;

-- Grant minimal permissions required to read data and use compute
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE STREAMLIT_ROLE;
GRANT USAGE ON DATABASE IMDB_DB TO ROLE STREAMLIT_ROLE;
GRANT USAGE ON SCHEMA IMDB_DB.PUBLIC TO ROLE STREAMLIT_ROLE;
GRANT SELECT ON VIEW IMDB_DB.PUBLIC.v_clean_movies TO ROLE STREAMLIT_ROLE;

-- Create the user (Replace with secure password)
CREATE USER IF NOT EXISTS streamlit_app_user
    PASSWORD = '<YourSecurePassword>' -- Enter your Password
    DEFAULT_ROLE = STREAMLIT_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH
    MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE STREAMLIT_ROLE TO USER streamlit_app_user;


-- ------------------------------------------------------------------------------
-- 6. AUTOMATED CDC INGESTION TASK (Upsert)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE TASK weekly_movie_refresh_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 4 * * 0 UTC'
AS
BEGIN
  -- 1. Clear out the staging area
  TRUNCATE TABLE stg_imdb_titles;
  TRUNCATE TABLE stg_imdb_countries;
  
  -- 2. Load fresh S3 data into STAGING
  COPY INTO stg_imdb_titles
  FROM @my_s3_imdb_stage/title_basics/
  PATTERN = '.*title.basics.tsv.gz'
  FORCE = TRUE
  ON_ERROR = 'CONTINUE';
  
  COPY INTO stg_imdb_countries
  FROM @my_s3_imdb_stage/title_akas/
  PATTERN = '.*title.akas.tsv.gz'
  FORCE = TRUE
  ON_ERROR = 'CONTINUE';

  -- 3. Merge Titles into Production
  MERGE INTO imdb_titles AS target
  USING stg_imdb_titles AS source
  ON target.tconst = source.tconst
  WHEN MATCHED AND (
      target.primaryTitle != source.primaryTitle OR 
      target.startYear != source.startYear OR
      target.runtimeMinutes != source.runtimeMinutes OR
      target.genres != source.genres
  ) THEN 
      UPDATE SET 
          target.primaryTitle = source.primaryTitle,
          target.startYear = source.startYear,
          target.runtimeMinutes = source.runtimeMinutes,
          target.genres = source.genres
  WHEN NOT MATCHED THEN 
      INSERT (tconst, titleType, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres)
      VALUES (source.tconst, source.titleType, source.primaryTitle, source.originalTitle, source.isAdult, source.startYear, source.endYear, source.runtimeMinutes, source.genres);

  -- 4. Merge Countries into Production
  MERGE INTO imdb_countries AS target
  USING stg_imdb_countries AS source
  ON target.titleId = source.titleId AND target.ordering = source.ordering
  WHEN NOT MATCHED THEN
      INSERT (titleId, ordering, title, region, language, types, attributes, isOriginalTitle)
      VALUES (source.titleId, source.ordering, source.title, source.region, source.language, source.types, source.attributes, source.isOriginalTitle);
END;

-- Uncomment the line below to activate the schedule
-- ALTER TASK weekly_movie_refresh_task RESUME;
