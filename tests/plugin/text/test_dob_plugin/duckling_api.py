import requests
import json
import datetime

DUCKLING_HOST = "localhost:8000"
LOCALE = "en_US"
TIMEZONE = "America/New_York"
DIMENSIONS = ["date"]

def get_entities_from_duckling(text):
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    reftime = int(datetime.datetime.now().timestamp() * 1000)  # Use the current timestamp

    duckling_req_payload = {
        "text": text,
        "locale": LOCALE,
        "tz": TIMEZONE,
        "dims": json.dumps(DIMENSIONS),
        "reftime": reftime,
        "latent": True,
    }
    response = requests.post(
        f"http://{DUCKLING_HOST}/parse",
        headers=headers,
        data=duckling_req_payload,
    )
    if response:
        # Parse the JSON response
        json_response = json.loads(response.text)

        # Find the dictionary with 'dims' equal to 'time' or 'date'
        for entry in json_response:
            if entry.get('dim') in ['time', 'date']:

                # Access the 'value' of the first 'values'
                json_response = entry.get('value', {}).get('values', [{}])[0].get('value')
                

                return json_response
    else:
        print("empty duckling response for:",text)
    return "dim = time not found!"