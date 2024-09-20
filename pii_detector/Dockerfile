FROM python:3.9

RUN apt update
RUN apt install tree
RUN apt install sshpass

ADD requirements.txt .
RUN pip3 install -r requirements.txt

RUN python3 -m spacy download en_core_web_lg
RUN python3 -m spacy download en_core_web_trf

WORKDIR /src
ENV PYTHONPATH=/src

ADD src /src

RUN python manage.py collectstatic --noinput

ENTRYPOINT ["python3", "manage.py", "runserver", "0.0.0.0:8000"]