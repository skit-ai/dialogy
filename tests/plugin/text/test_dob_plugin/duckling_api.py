# import requests
# import json

# DUCKLING_HOST = "localhost:8000"

# def create_duckling_payload(
#     text: str,
#     dimensions: list = [],
#     reference_time=None,
#     locale=" ",
#     use_latent=False,
#     timezone: str = "America/New_York"
# ):

#     payload = {
#         "text": text,
#         "locale": locale,
#         "tz": timezone,
#         "dims": json.dumps(dimensions),
#         "reftime": reference_time,
#         "latent": use_latent,
#     }

#     return payload


# def get_entities_from_duckling(text, reftime, dimensions, locale, timezone):

#     headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

#     duckling_req_payload = create_duckling_payload(
#         text=text,
#         dimensions=dimensions,
#         reference_time=reftime,
#         locale=locale,
#         use_latent=True,
#         timezone=timezone,
#     )

#     response = requests.post(
#         f"http://{DUCKLING_HOST}/parse",
#         headers=headers,
#         data=duckling_req_payload,
#     )
#     return response

# import datetime 

# dimensions = ["date"]
# text = "October 20th, 1960"
# reftime = int(datetime.datetime.now().timestamp() * 1000)  # Use the current timestamp
# locale = "en_US"
# timezone = "America/New_York"

# payload = create_duckling_payload(text, dimensions, reftime, locale, timezone)
# response = get_entities_from_duckling(text, reftime, dimensions, locale, timezone)
# print(response.text)
# # Now 'response' contains the entities extracted by Duckling
# import re

# def _class_5(transcript):
#     """
#     input: transcript that looks like-"xx:yy "
#     description: replace ":" with " "; if yy = 00 or 0y: replace yy with "  " or if 0y, replace 0 with ""
#     output: xx yy
#     """
#     # Using regular expressions to extract hours and minutes
#     # match = re.match(r'\b(\d{1,2}):(\d{2})\b', transcript)
    

#     # Your regex pattern
#     pattern = re.compile(r'\b(\d{1,2}):(\d{2})\b')

#     match = pattern.search(transcript)
#     # pattern = re.compile(r'\b(\d{1,2}):(\d{2})\b')
#     # matches = pattern.findall(transcript)
#     # print

#     if match:
#         hours, minutes = match.groups()
#         start_idx, hours_end = match.start(1), match.end(1)
#         minutes_start, end_idx = match.start(2), match.end(2)
        
#         # # Removing leading zeros from hours and minutes
#         # hours = str(int(hours))
#         # minutes = str(int(minutes))
        
#         # Modifying the minutes based on the conditions
#         if minutes == "00":
#             minutes = " "
#         elif minutes.startswith("0"):
#             minutes = "" + minutes[1]
        
#         # Combining the modified hours and minutes
#         result = hours + " " + minutes
#         transformed_transcript = transcript[:start_idx] + result + transcript[end_idx:]
#         return transformed_transcript

#     else:
#         # Handle invalid input
#         return "Invalid input format"

# # example test cases
# case1 = "jefgljl 12:45 12:"
# case2 = "12:00"
# case3 = "12:09"
# case4 = "1:26"

# print(_class_5(case1))  # Output: "12 45"
# print(_class_5(case2))  # Output: "12 "
# print(_class_5(case3))  # Output: "12 9"
# print(_class_5(case4))  # Output: "1 26"

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

    # Parse the JSON response
    json_response = json.loads(response.text)

    # Find the dictionary with 'dims' equal to 'time' or 'date'
    for entry in json_response:
        if entry.get('dim') in ['time', 'date']:

            # Access the 'value' of the first 'values'
            json_response = entry.get('value', {}).get('values', [{}])[0].get('value')
            

            return json_response
    return "dim = time not found!"
