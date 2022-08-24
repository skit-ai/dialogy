from typing import Dict, Union, Optional
import requests

from loguru import logger


class MapMyIndia:
    def __init__(self, client_id: Optional[str], client_secret: Optional[str]) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self._get_token()

    def _get_token(self) -> str:
        token = requests.post(
            "https://outpost.mapmyindia.com/api/security/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        ).json()

        return token["access_token"]

    def geocode(
        self, address: str, region: str = "ind", pin: Optional[str] = None
    ) -> Union[Dict[str, str], None]:  # aiohttp
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
