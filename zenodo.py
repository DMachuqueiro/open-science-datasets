"""Acesso HTTP ao Zenodo: https://developers.zenodo.org/#records."""

from urllib.parse import parse_qs, urlsplit

import requests

from metadata import as_dict, normalize_zenodo_record, record_identifier, safe_url
from models import SearchPage

API_URL = "https://zenodo.org/api/records/"
RESULT_LIMIT = 20
REQUEST_TIMEOUT = 10
INVALID_RESPONSE = "A API do Zenodo devolveu uma resposta inválida. Tenta novamente mais tarde."


class ZenodoError(Exception):
    """Falha com uma mensagem adequada à interface."""

    status_code = 502


class ZenodoNotFound(ZenodoError):
    status_code = 404


class ZenodoTimeout(ZenodoError):
    status_code = 504


def _get_json(url, params=None, detail=False):
    try:
        response = requests.get(
            url, params=params, headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        if detail and response.status_code == 404:
            raise ZenodoNotFound("O registo não foi encontrado no Zenodo.")
        response.raise_for_status()
    except requests.Timeout as exc:
        raise ZenodoTimeout(
            "O Zenodo demorou demasiado tempo a responder. Tenta novamente."
        ) from exc
    except requests.RequestException as exc:
        raise ZenodoError(
            "Não foi possível consultar a API do Zenodo. Tenta novamente mais tarde."
        ) from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise ZenodoError(INVALID_RESPONSE) from exc
    if not isinstance(payload, dict):
        raise ZenodoError(INVALID_RESPONSE)
    return payload


def _linked_page(value, expected):
    url = safe_url(value)
    if url and expected > 0:
        parsed = urlsplit(url)
        if (parsed.scheme == "https" and parsed.netloc == "zenodo.org"
                and parsed.path.rstrip("/") == "/api/records"
                and parse_qs(parsed.query).get("page") == [str(expected)]):
            return expected
    return None


def search_datasets(query, page=1):
    query = query.strip()
    result = SearchPage(page=page)
    if not query:
        return result
    payload = _get_json(API_URL, {
        "q": query, "type": "dataset", "size": RESULT_LIMIT, "page": page,
    })
    hits = as_dict(payload.get("hits"))
    records = hits.get("hits")
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise ZenodoError(INVALID_RESPONSE)
    result.results = [normalize_zenodo_record(item) for item in records[:RESULT_LIMIT]]

    total = hits.get("total")
    if type(total) is int and total >= 0:
        result.total, result.total_is_exact = total, True
    elif (isinstance(total, dict) and type(total.get("value")) is int
            and total["value"] >= 0 and total.get("relation") in ("eq", "gte")):
        result.total = total["value"]
        result.total_is_exact = total.get("relation") == "eq"

    # As ligações da API têm precedência sobre cálculos a partir do total.
    links = payload.get("links")
    if isinstance(links, dict):
        result.previous_page = _linked_page(links.get("prev"), page - 1)
        result.next_page = _linked_page(links.get("next"), page + 1)
    elif result.total_is_exact:
        if page > 1 and (page - 2) * RESULT_LIMIT < result.total:
            result.previous_page = page - 1
        if result.results and page * RESULT_LIMIT < result.total:
            result.next_page = page + 1
    return result


def get_dataset(identifier):
    identifier = record_identifier(identifier)
    if identifier is None:
        raise ZenodoNotFound("O identificador do registo Zenodo é inválido.")
    payload = _get_json(API_URL + identifier, detail=True)
    if "id" not in payload and "metadata" not in payload:
        raise ZenodoError(INVALID_RESPONSE)
    resource_type = as_dict(as_dict(payload.get("metadata")).get("resource_type")).get("type")
    if isinstance(resource_type, str) and resource_type and resource_type != "dataset":
        raise ZenodoNotFound("Este registo do Zenodo não corresponde a um dataset.")
    return normalize_zenodo_record(payload)
