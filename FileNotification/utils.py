import requests
import os
import json

def download_file(url, local_filename):
    # Download the file
    with requests.get(url, stream=True) as r:
        if r.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"File downloaded successfully: {local_filename}")
        else:
            print(f"Error downloading file: {r.status_code}")

def get_pii_timestamps(local_filename):
    timestamps = []
    json_data = {}
    try:
        with open(local_filename, 'r') as f:
            json_data = json.load(f)
    except json.JSONDecodeError as e:
        print("Json file load failed:", e)
        return timestamps

    items = json_data['results']['items']
    for item in items:
        time = {}
        if item['alternatives']:
            alternatives = item['alternatives']
            for alternative in alternatives:
                if alternative['content'] == "[PII]":
                    time['start_time'] = item['start_time']
                    time['end_time'] = item['end_time']
                    timestamps.append(time)
    print(timestamps)
    return timestamps;