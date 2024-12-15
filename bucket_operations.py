import csv
import io
import tempfile
from google.cloud import storage
from striprtf.striprtf import rtf_to_text


def initialize_client():
    return storage.Client()

def read_csv_from_bucket(bucket_name, file_name):
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    csv_content = blob.download_as_text()
    csv_reader = csv.reader(io.StringIO(csv_content))
    csv_data = [row for row in csv_reader]
    return csv_data

def read_files_from_bucket(config, bucket_name, folder=None):
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    if folder:
        prefix = folder if folder.endswith('/') else f"{folder}/"
        blobs = bucket.list_blobs(prefix=prefix)
    else:
        blobs = bucket.list_blobs()
    formatted_rtf_html = ""
    csv_data = []
    person_image = None
    for blob in blobs:
        if blob.name.lower().endswith('.rtf'):
            rtf_content = blob.download_as_text()
            plain_text_rtf = rtf_to_text(rtf_content)
            formatted_rtf_html = plain_text_rtf.replace('\n', '<br>')
        elif blob.name.lower().endswith('.csv'):
            csv_content = blob.download_as_text()
            csv_reader = csv.reader(io.StringIO(csv_content))
            csv_data = [row for row in csv_reader]
        elif blob.name.lower().endswith(('.jpeg', '.jpg', '.png')):
            person_image = blob.download_as_bytes()
    return formatted_rtf_html, csv_data, person_image

import os

def read_news_and_combine(bucket_name, folder = "news/"):
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder)  

    result_list = []
    for filename in blobs:
        if filename.name.lower().endswith('.txt'):
            lines = filename.download_as_text().split("\n")
            parsed_data = {
                    "news_name": lines[0].strip(),  
                    "source": lines[1].split(":", 1)[1].strip() if ":" in lines[1] else None,
                    "published_at": lines[2].split(":", 1)[1].strip() if ":" in lines[2] else None,
                    "url": lines[3].split(":", 1)[1].strip() if ":" in lines[3] else None,
                    "coordinates": lines[4].split(":", 1)[1].strip() if ":" in lines[4] else None,
                }
            result_list.append(parsed_data)
    return result_list


# Upload a file to a bucket, optionally within a specific folder
def upload_csv_to_gcs(bucket_name, destination_blob_name, dataframe):
    # Convert the DataFrame to a CSV in-memory
    csv_buffer = io.StringIO()
    dataframe.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Create a GCS client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload the CSV file
    blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
    print(f"File uploaded to {bucket_name}/{destination_blob_name}")


def upload_image_to_gcs(bucket_name, image, destination_blob_name):
    """
    Uploads an in-memory image to a GCS bucket.

    :param bucket_name: Name of the GCS bucket.
    :param uploaded_file: File-like object containing the image (from upload).
    :param destination_blob_name: The name of the object in the bucket.
    """
    try:
        # Save the image to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            image.save(temp_file.name, format="PNG")
            temp_file_path = temp_file.name

        # Create a storage client
        storage_client = storage.Client()

        # Get the bucket
        bucket = storage_client.bucket(bucket_name)

        # Create a blob object
        blob = bucket.blob(destination_blob_name)

        # Upload the temporary file to GCS
        blob.upload_from_filename(temp_file_path)

        print(f"File uploaded to {destination_blob_name} in bucket {bucket_name}.")
    except Exception as e:
        print(f"Error occurred: {e}")
