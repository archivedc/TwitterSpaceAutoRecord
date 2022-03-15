FROM debian AS git

RUN apt-get update && apt-get -y install git

WORKDIR /app

RUN git clone --depth 1 https://github.com/archivedc/RecordTwitterSpace.git RecordTwitterSpace
RUN git clone --depth 1 -b tw-frontapi https://github.com/mkaraki/WatchTweets.git WatchTweets

FROM python:3.9-bullseye

RUN apt-get update && apt-get -y install libgsl-dev ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install requirements
COPY --from=git /app/RecordTwitterSpace/ /app/RecordTwitterSpace
COPY --from=git /app/WatchTweets/ /app/WatchTweets

# Copy application
COPY main.py /app/main.py

# Install initial configuration file
COPY .env.sample /app/.env

# Install python requirements
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt \
    -r RecordTwitterSpace/requirements.txt \
    -r WatchTweets/requirements.txt 
