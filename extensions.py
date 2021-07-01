from __future__ import annotations

from typing import Any, Mapping

import requests
import toolz  # type: ignore


class Converter:
    def __init__(
        self, url: str, params: Mapping[str, str], currencies_mapping: Mapping[str, str]
    ) -> None:
        self._url = url
        self._params = params
        self._currencies_mapping = currencies_mapping

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> Converter:
        return cls(
            url=config["url"],
            params=config["params"],
            currencies_mapping=config["currencies_mapping"],
        )

    def convert(self, source: str, target: str, amount: float) -> float:
        if source not in self._currencies_mapping:
            raise APIException(f'Невозможно обработать валюту "{source}"')
        if target not in self._currencies_mapping:
            raise APIException(f'Невозможно обработать валюту "{target}"')
        query = f"{self._currencies_mapping[source]}_{self._currencies_mapping[target]}"
        response = requests.get(
            self._url,
            params=toolz.merge(
                self._params,
                {"q": query},
            ),
        )
        response.raise_for_status()
        return response.json()[query] * amount


class APIException(Exception):
    pass
