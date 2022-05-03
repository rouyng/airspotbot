FROM python:3.7-alpine
COPY . /src
WORKDIR /src
RUN apk add --no-cache --virtual .build-deps gcc libc-dev libffi-dev rust cargo openssl-dev
RUN apk add chromium chromium-chromedriver
RUN pip3 install -r requirements.txt
RUN apk del .build-deps

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/

CMD ["python3", "-m", "airspotbot"]