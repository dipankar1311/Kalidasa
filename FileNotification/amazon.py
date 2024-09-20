from Pii_Transcribe import process
import os

def make_request(params):
    print("Making request to amazon")
    print("========================")
    print(f"{params=}") 
    #os.rename(f"Downloads/{params}", 'Downloads/webex_recording.mp4') 
    #process('webex_recording.mp4')
    process(params)
