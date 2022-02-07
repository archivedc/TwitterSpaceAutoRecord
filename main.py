import time
import os
import re
import json
from pathlib import Path

from dotenv import load_dotenv
import ffmpeg

from RecordTwitterSpace import main as rec
from WatchTweets import main as watch


def queueRecord(stream_url, filename):
    i = ffmpeg.input(stream_url)
    cmd = i.output(filename)
    cmd.run_async(pipe_stdin=False)


def record(space_id):
    metadata, admins, streaming_url = None, None, None
    try:
        metadata, admins, streaming_url = rec.getStreamingUrl(space_id)
    except:
        print('[INFO] Failed to get streaming url. Maybe the space is ended.')
        return False

    space_state = metadata['state']

    if (space_state != 'Running'):
        print('[INFO] Space is ended.')
        return False

    dirname, filename = rec.generate_filename(metadata, admins)

    Path(dirname).mkdir(parents=True, exist_ok=True)

    queueRecord(streaming_url, os.path.join(dirname, filename))
    print('[INFO] Queued: ' + filename)


def process_spaceurl(url):
    space_id = re.sub(
        r'^https?://twitter.com/i/spaces/([a-zA-Z0-9]+)(/.+$)?', r'\1', url)
    print('[INFO] Found: ' + space_id)
    record(space_id)


def process_tweet(tweet):
    if ('entities' in tweet and 'urls' in tweet['entities']):
        for url in tweet['entities']['urls']:
            if ('expanded_url' in url):
                if url['expanded_url'].startswith('https://twitter.com/i/spaces/'):
                    process_spaceurl(url['expanded_url'])
                    return True


def process_tweets(tweets):
    for tweet in tweets:
        process_tweet(tweet)


if __name__ == '__main__':
    load_dotenv(override=True)

    q = os.getenv('QUERY') + ' -is:retweet twitter.com/i/spaces'

    lastsidpath = './last_sid.json'
    stime = None

    if (os.path.exists(lastsidpath)):
        with open(lastsidpath, 'r') as f:
            j = json.load(f)
            if ('stime' in j):
                stime = j['stime']

    client_time = time.time()
    watch_client = watch.getClient()

    while True:
        if (time.time() - 600 > client_time):
            print('[INFO] Update tokens')
            watch_client.guest_token = watch_client.generate_token()[
                'guest_token']
            watch_client.headers['x-guest-token'] = watch_client.guest_token
            client_time = time.time()

        tstime = stime
        stime, res = watch.getAllNewTweets(watch_client, q, stime=stime)

        if (len(res) > 0):
            process_tweets(res.values())

        # Save last id
        if (stime != None):
            with open(lastsidpath, 'w') as f:
                json.dump({'stime': stime}, f)
        else:
            # If cannot got any last id information,
            # Re-use last id information from last polling.
            stime = tstime

        time.sleep(30)
