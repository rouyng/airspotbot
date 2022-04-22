FROM python:3.7-slim-buster
COPY . /src
RUN pip3 install -r /src/requirements.txt
RUN apt install chromium chromium-chromedriver
WORKDIR /src

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/

CMD ["python3", "-m", "airspotbot"]