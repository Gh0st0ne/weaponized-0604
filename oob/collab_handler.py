
import time
import json
import requests

current_collaborators = []

def generate():
    res = requests.get('http://127.0.0.1:8000/generatePayload')
    assert res.status_code == 200, "generate Error"
    payload_full = res.text
    return payload_full

# expect jsonlines with DNS records
def collect(payload):
    res = requests.get('http://127.0.0.1:8000/fetchFor', params=dict(payload=payload))
    assert res.status_code == 200, "fetch Error"
    return map(json.loads, filter(None, res.text.strip().split('\n')))

def poll(payload, decoder):
    print('payload: %s' % payload)
    shelves = []
    lastUpdated = time.time()
    # stop collecting if data isn't back during 60 seconds
    while time.time() - lastUpdated <= 60:
        data = collect(payload)
        if len(data) != 0:
            # cumulate result data
            shelves.extend(data)
            # get current output
            output = decoder.decode(shelves)
            lastUpdated = time.time()
            yield output
        time.sleep(1)

if __name__ == "__main__":
    import sys
    import decoder as myDec
    payload = generate()
    print(payload)
    pl = payload[:payload.find('.')]
    for current_result in poll(pl, myDec):
        sys.stdout.write('\r%s' % current_result)
        sys.stdout.flush()

