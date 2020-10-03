FROM python:3.7-slim-buster
COPY . /src
RUN pip3 install -r /src/requirements.txt
WORKDIR /src
CMD ["python3", "-m", "airspotbot"]