import requests

from loguru import logger


class MapMyIndia:
    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self._get_token()

    def _get_token(self):
        token = requests.post(
            "https://outpost.mapmyindia.com/api/security/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        ).json()

        return token["access_token"]

    def text_search(self, query, region="ind", pin=None, location=None):
        url = "https://atlas.mapmyindia.com/api/places/textsearch/json?"

        params = {
            "query": query,
            "region": region,
        }
        if pin:
            params["filter"] = f"pin:{pin}"

        if location:
            params["location"] = location

        try:
            addresses = requests.get(
                url,
                params=params,
                headers={"Authorization": "bearer " + self.access_token},
            ).json()

        except Exception as e:
            logger.debug(f"MMI API: Address not found for input {params}")
            addresses = None

        return addresses

    def geocode(self, address, region="ind", pin=None): #aiohttp
        url = "https://atlas.mapmyindia.com/api/places/geocode?"

        params = {
            "address": address,
            "region": region,
        }
        if pin:
            params["bound"] = f"{pin}"

        try:
            addresses = requests.get(
                url,
                params=params,
                headers={"Authorization": "bearer " + self.access_token},
            ).json()

        except Exception as e:
            logger.debug(f"MMI API: Address not found for input {params}")
            addresses = None

        return addresses
