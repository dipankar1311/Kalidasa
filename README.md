To run react audio file

Prerequisite:
Make sure AWS keys have authorization to access amazon s3, amazon transcribe API

1. Fill AWS details like access_key_id, secret_access_key, bucket_name in config.json
2. go to FileNotification folder and run
    python FileChangeNotification.py Downloads/
    Downloads folder is the one where you will copy original audio file
3. copy original file to Downloads/ folder




Flow and initial PoCs slides here: 
IntelligentAudioRedactionAndLiveCallAlert​.pptx


Vidcast: https://app.vidcast.io/share/7ff04e5f-1e26-4dc0-a51e-97f7ef4c3043

1. Start our NLP Engine and NGINX Reverse Proxy. Here we are using a Expressway TTM Box's Server Certificate so ignore the certificate warning.

```
docker run --rm -it $(docker build -q .)
```

2. Start RASA Server

```
rasa run --enable-api
```

3. Navigate to the HTTPS url for the machine from where the Code is executed.