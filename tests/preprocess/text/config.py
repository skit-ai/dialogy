mock_date_entity = {
    "body": "on 27th next month",
    "start": 21,
    "value": {
        "values": [
            {
                "value": "2021-01-27T00:00:00.000-08:00",
                "grain": "day",
                "type": "value",
            }
        ],
        "value": "2021-01-27T00:00:00.000-08:00",
        "grain": "day",
        "type": "value",
    },
    "end": 39,
    "dim": "time",
    "latent": False,
}

mock_unknown_entity = {
    "body": "3 foobars",
    "start": 67,
    "value": {"value": 3, "type": "foobar", "unit": "person"},
    "end": 75,
    "dim": "number",
    "latent": False,
}
