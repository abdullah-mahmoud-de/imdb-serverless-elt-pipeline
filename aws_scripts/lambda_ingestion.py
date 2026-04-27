# Python code for the Lambda function

import boto3
import urllib.request

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # IMDb daily updated non-commercial dataset
    base_url = "https://datasets.imdbws.com/"

    files = [
        "title.basics.tsv.gz",
        "title.akas.tsv.gz"
    ]

    bucket_name = "imdb-raw-data-lake-2026"

    for file in files:
        # Dynamically place them in distinct folders (title_basics/ and title_akas/)
        folder = file.split(".tsv")[0].replace('.', '_')
        s3_key = f"{folder}/{file}"
        url = f"{base_url}{file}"

        print(f"Starting stream from *{url}* to *{bucket_name}/{s3_key}*")

        try:
            # Stream the file directly to S3 using upload_fileobj
            # This bypasses Lambda's internal storage limits
            req = urllib.request.urlopen(url)
            s3_client.upload_fileobj(req, bucket_name, s3_key)
            print(f"Success: {file} safely landed in S3.")

        except Exception as e:
            print(f"Error streaming {file}: {str(e)}")
            raise e
    return {
        'statusCode': 200,
        'body': "Targeted IMDb ingestion completed successfully."
    }
