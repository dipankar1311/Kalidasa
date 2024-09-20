import json
import boto3
import subprocess
import os
import uuid
from botocore.exceptions import ClientError
import pdb
import time
from utils import download_file, get_pii_timestamps
from math import floor, ceil

def upload_transcribe_and_process_mp4_with_pii_detection_timestamps(json_file_path, input_file_name):
    # Upload the MP4 file to S3
    print("Progressing.........")
    with open(json_file_path, 'r') as f:
        json_data = json.load(f)

    credentials = json_data['credentials']
    access_key_id = credentials['access_key_id']
    secret_access_key = credentials['secret_access_key']
    region_name = "ap-south-1"
    #pdb.set_trace()
    s3_client = boto3.client('s3',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region_name
    )

    file_info = json_data['file_info']
    bucket_name = file_info['bucket_name']

    original_file_path = os.path.join(os.getcwd() + "/Downloads/", input_file_name)
    print("we passed the paths.....:" + original_file_path)
    s3_client.upload_file(original_file_path, bucket_name, input_file_name)

    # Transcribe the uploaded MP4 file with PII detection
    transcribe_client = boto3.client('transcribe',
                                     region_name = region_name)

    job_name = 'my-transcribe-job' + str(uuid.uuid4())
    print("job_name: " + job_name)
    media_file_uri = f"https://{bucket_name}.s3.amazonaws.com/{input_file_name}"

    try:
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={
                'MediaFileUri': media_file_uri
            },
            LanguageCode='en-US',
	        ContentRedaction = {
		     'RedactionOutput':'redacted',
		     'RedactionType':'PII',
		     'PiiEntityTypes': ['ALL']
		      }
        )
        print(f"Transcription job started: {response['TranscriptionJob']['TranscriptionJobName']}")
    except ClientError as e:
        print(f"Error starting transcription job: {e}")

    # Download the transcription job transcript
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName = job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            transcription_output = status['TranscriptionJob']['Transcript']['RedactedTranscriptFileUri']
            #transcribe_bucket_name, transcribe_file_path = transcription_output.split('/', 1)
            # Download the transcribed JSON file
            #s3_client.download_file(transcribe_bucket_name, transcribe_file_path, 'transcribed.json')
            download_file(transcription_output, 'transcribe_output.json')
            print(status)
            break
        print("Not ready yet...")
        time.sleep(15)
        print(status)

    pii_timestamps = get_pii_timestamps('transcribe_output.json')
    if (len(pii_timestamps)):
        output_file = f"processed_{input_file_name}"
        if os.path.isfile(output_file):
            os.remove(output_file)
        command = f"ffmpeg -i {original_file_path} -af " 
        volume_command = ""
        for pii_time in pii_timestamps:
            start_time = round(float(pii_time['start_time']))
            end_time = round(float(pii_time['end_time']))
            if start_time == end_time:
                end_time = start_time + 1
            duration = round(end_time - start_time)
            if volume_command:
                volume_command += ","
            volume_command += f"volume=enable='between(t,{start_time},{end_time})':volume=0[main];sine=d={duration}:f=800,adelay={start_time}s,pan=stereo|FL=c0|FR=c0[beep];[main][beep]amix=inputs=2"
        command +=  volume_command + " " + output_file
        print(command)
        subprocess.run(command.split(), check=True)
        print("processed file generated")
    else:
        print("No PII in the file recorded")

    #./ffmpeg -i pii-test-fie1.mp4 -af "volume=enable='between(t,33.029,35.909)':volume=0" pii-test-fie1-output.mp4
    #ffmpeg -i pii-test-fie1.mp4 -filter_complex "[0]volume=0:enable='between(t,33,36)'[main];sine=d=5:f=800,adelay=10s,pan=stereo|FL=c0|FR=c0[beep];[main][beep]amix=inputs=2" output_test.mp4
    #ffmpeg -i pii-test-fie1.mp4 -af "volume=enable='between(t,{start},{end})':volume=0[main];sine=d={duration}:f=800,adelay={start}s,pan=stereo|FL=c0|FR=c0[beep];[main][beep]amix=inputs=2" {output_file}



if __name__ == '__main__':
    json_file_path = 'config.json'
    upload_transcribe_and_process_mp4_with_pii_detection_timestamps(json_file_path, "pii-test-fie1.mp4")

def process(input_file_name):
    json_file_path = 'config.json'
    print("InProgress............")
    upload_transcribe_and_process_mp4_with_pii_detection_timestamps(json_file_path, input_file_name)


