mock_number_entity = {
    "body": "four",
    "start": 7,
    "value": {"value": 4, "type": "value"},
    "end": 11,
    "dim": "number",
    "latent": False,
}

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

mock_time_entity = {
    "body": "at 5 am",
    "start": 55,
    "value": {
        "values": [
            {
                "value": "2020-12-24T05:00:00.000-08:00",
                "grain": "hour",
                "type": "value",
            },
            {
                "value": "2020-12-25T05:00:00.000-08:00",
                "grain": "hour",
                "type": "value",
            },
            {
                "value": "2020-12-26T05:00:00.000-08:00",
                "grain": "hour",
                "type": "value",
            },
        ],
        "value": "2020-12-24T05:00:00.000-08:00",
        "grain": "hour",
        "type": "value",
    },
    "end": 62,
    "dim": "time",
    "latent": False,
}

mock_interval_entity = {
    "body": "between 2 to 4 am",
    "start": 0,
    "value": {
        "values": [
            {
                "to": {
                    "value": "2021-01-22T05:00:00.000+05:30",
                    "grain": "hour",
                },
                "from": {
                    "value": "2021-01-22T02:00:00.000+05:30",
                    "grain": "hour",
                },
                "type": "interval",
            },
            {
                "to": {
                    "value": "2021-01-23T05:00:00.000+05:30",
                    "grain": "hour",
                },
                "from": {
                    "value": "2021-01-23T02:00:00.000+05:30",
                    "grain": "hour",
                },
                "type": "interval",
            },
            {
                "to": {
                    "value": "2021-01-24T05:00:00.000+05:30",
                    "grain": "hour",
                },
                "from": {
                    "value": "2021-01-24T02:00:00.000+05:30",
                    "grain": "hour",
                },
                "type": "interval",
            },
        ],
        "to": {"value": "2021-01-22T05:00:00.000+05:30", "grain": "hour"},
        "from": {"value": "2021-01-22T02:00:00.000+05:30", "grain": "hour"},
        "type": "interval",
    },
    "end": 17,
    "dim": "time",
    "latent": False,
}

mock_people_entity = {
    "body": "3 people",
    "start": 67,
    "value": {"value": 3, "type": "value", "unit": "person"},
    "end": 75,
    "dim": "people",
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
