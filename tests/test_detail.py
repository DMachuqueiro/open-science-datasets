"""Dados simulados apenas para verificar o detalhe e a normalização."""

import unittest
from unittest.mock import Mock, patch

import requests

from app import app
from metadata import normalize_zenodo_record, safe_url
from zenodo import API_URL, REQUEST_TIMEOUT


class DetailTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        patcher = patch("zenodo.requests.get")
        self.get = patcher.start()
        self.addCleanup(patcher.stop)
        self.get.return_value = Mock(status_code=200)
        self.record = {
            "id": 123,
            "updated": "2026-10-01T12:00:00Z",
            "doi_url": "https://doi.org/10.5281/zenodo.123",
            "links": {"self_html": "https://zenodo.org/records/123"},
            "metadata": {
                "title": "Dataset de teste",
                "description": "<p>Descrição completa &amp; segura.</p>" + " dados" * 100,
                "resource_type": {"type": "dataset"},
                "creators": [{"name": "Autora", "affiliation": "Universidade", "orcid": "0000-0000-0000-0000"}],
                "doi": "10.5281/zenodo.123",
                "publication_date": "2026-09-01",
                "keywords": ["clima", "oceanos"],
                "license": {"id": "cc-by-4.0", "title": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
                "access_right": "embargoed",
                "access_conditions": "<p>Acesso após o embargo.</p>",
                "embargo_date": "2027-01-01",
                "related_identifiers": [
                    {"identifier": "https://example.org/project", "relation": "isPartOf", "resource_type": "other"},
                    {"identifier": "10.1234/example", "relation": "isSupplementTo", "scheme": "doi"},
                ],
            },
            "files": [{"key": "data.csv", "size": 0, "type": "csv", "links": {
                "self": "https://zenodo.org/api/records/123/files/data.csv/content",
            }}],
        }
        self.get.return_value.json.return_value = self.record

    def detail(self, params=None, status=200, headers=None):
        response = self.client.get("/datasets/zenodo/123", query_string=params, headers=headers)
        self.assertEqual(response.status_code, status)
        return response.get_data(as_text=True)

    def test_direct_detail_requests_only_the_record(self):
        page = self.detail()
        self.get.assert_called_once_with(
            API_URL + "123", params=None,
            headers={"Accept": "application/json"}, timeout=REQUEST_TIMEOUT,
        )
        self.assertIn("Dataset de teste", page)
        self.assertIn('href="/">Pesquisar datasets</a>', page)
        self.assertIn('aria-label="Link para o registo original no Zenodo: Dataset de teste">Link</a>', page)

    def test_modal_uses_the_same_safe_metadata_without_page_wrapper(self):
        self.record["metadata"]["description"] = '<script>danger()</script>Texto &lt;img src=x&gt;'
        page = self.detail(headers={"X-Requested-With": "fetch"})
        self.assertNotIn("<!DOCTYPE", page)
        self.assertNotIn("<main>", page)
        self.assertNotIn("Voltar à pesquisa", page)
        self.assertIn("Dataset de teste", page)
        self.assertIn(">Link</a>", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<img", page)
        self.assertIn("&lt;img", page)
        self.get.assert_called_once()

    def test_modal_preserves_not_found_and_api_error_statuses(self):
        self.get.return_value = Mock(status_code=404)
        page = self.detail(status=404, headers={"X-Requested-With": "fetch"})
        self.assertIn('role="alert"', page)
        self.assertIn("O registo não foi encontrado", page)
        self.assertNotIn("<!DOCTYPE", page)
        self.get.side_effect = requests.Timeout()
        page = self.detail(status=504, headers={"X-Requested-With": "fetch"})
        self.assertIn("demorou demasiado tempo", page)
        self.assertNotIn("<!DOCTYPE", page)

    def test_detail_presents_full_metadata_and_explicit_links(self):
        page = self.detail()
        for value in ("Zenodo", "Autora", "Universidade", "0000-0000-0000-0000",
                      "10.5281/zenodo.123", "2026-09-01", "2026-10-01T12:00:00Z",
                      "clima", "oceanos", "CC BY 4.0", "embargoed", "2027-01-01",
                      "Acesso após o embargo.", "isPartOf", "data.csv", "csv"):
            with self.subTest(value=value):
                self.assertIn(value, page)
        self.assertIn('href="https://example.org/project"', page)
        self.assertIn('href="https://zenodo.org/api/records/123/files/data.csv/content"', page)
        self.assertIn("10.1234/example", page)
        self.assertNotIn('href="https://doi.org/10.1234/example"', page)
        self.assertNotIn('href="https://orcid.org/0000', page)
        self.assertIn(" dados" * 100, page)
        self.assertIn("Descrição completa &amp; segura.", page)
        self.assertNotIn("<p>", normalize_zenodo_record(self.record).description)

    def test_return_to_search_preserves_query_and_page(self):
        page = self.detail({"q": "clima & oceanos", "page": "3"})
        self.assertIn('href="/?q=clima+%26+oceanos&amp;page=3"', page)
        self.assertIn("Voltar à pesquisa — página 3", page)

    def test_invalid_origin_page_falls_back_to_one(self):
        page = self.detail({"q": "climate", "page": "invalid"})
        self.assertIn('href="/?q=climate&amp;page=1"', page)

    def test_missing_null_or_wrongly_typed_metadata_does_not_crash(self):
        for metadata in (None, [], {}, {"title": [], "description": {}, "license": 3,
                                       "creators": "author", "keywords": 2,
                                       "related_identifiers": False,
                                       "resource_type": {"type": []}}):
            with self.subTest(metadata=metadata):
                self.get.return_value.json.return_value = {"id": 123, "metadata": metadata, "files": None}
                page = self.detail()
                self.assertIn("Título não disponível.", page)
                self.assertIn("Autores não disponibilizados pela fonte.", page)
                self.assertIn("Ficheiros não disponibilizados pela fonte.", page)

    def test_missing_and_explicit_empty_values_remain_distinct(self):
        absent = normalize_zenodo_record({})
        empty = normalize_zenodo_record({"metadata": {
            "title": "", "description": "", "creators": [], "keywords": [],
            "doi": "", "related_identifiers": [],
        }, "files": []})
        for field in ("title", "description", "authors", "keywords", "doi", "files", "related_resources"):
            with self.subTest(field=field):
                self.assertIsNone(getattr(absent, field))
                self.assertIsNotNone(getattr(empty, field))
        self.get.return_value.json.return_value = {"id": 123, "metadata": {"description": "", "creators": []}, "files": []}
        page = self.detail()
        self.assertIn("Campo vazio na fonte.", page)
        self.assertIn("Nenhum autor indicado pela fonte.", page)
        self.assertIn("Nenhum ficheiro listado pela fonte.", page)

    def test_unexpected_nested_entries_do_not_crash(self):
        self.record["metadata"].update({
            "creators": [None, 1, {"name": [], "orcid": {}}],
            "keywords": [None, 2, "clima"],
            "related_identifiers": [None, {"identifier": [], "relation": {}}],
        })
        self.record["files"] = [None, {"key": [], "size": -1, "links": []}]
        page = self.detail()
        self.assertIn("clima", page)
        self.assertIn("Não disponibilizado pela fonte.", page)

    def test_zero_byte_file_is_preserved_and_missing_format_is_not_invented(self):
        del self.record["files"][0]["type"]
        dataset = normalize_zenodo_record(self.record)
        self.assertEqual(dataset.files[0].size, 0)
        self.assertIsNone(dataset.files[0].format)
        self.assertIn("<dd>0</dd>", self.detail())

    def test_explicit_author_url_is_linked(self):
        self.record["metadata"]["creators"][0]["orcid"] = "https://orcid.org/0000-0000-0000-0000"
        self.assertIn('href="https://orcid.org/0000-0000-0000-0000"', self.detail())

    def test_not_found_is_distinct_from_api_failure(self):
        self.get.return_value = Mock(status_code=404)
        page = self.detail(status=404)
        self.assertIn("O registo não foi encontrado", page)
        self.assertNotIn("Não foi possível consultar a API", page)

    def test_non_dataset_record_is_not_presented_as_a_dataset(self):
        self.record["metadata"]["resource_type"]["type"] = "software"
        self.assertIn("não corresponde a um dataset", self.detail(status=404))

    def test_invalid_identifiers_do_not_call_api(self):
        for identifier in ("abc", "0", "-1", "9" * 30):
            with self.subTest(identifier=identifier):
                self.assertEqual(self.client.get("/datasets/zenodo/" + identifier).status_code, 404)
        self.get.assert_not_called()

    def test_timeout_and_connection_errors_have_distinct_messages(self):
        for error, status, message in (
            (requests.Timeout(), 504, "demorou demasiado tempo"),
            (requests.ConnectionError(), 502, "Não foi possível consultar a API"),
        ):
            with self.subTest(error=error):
                self.get.side_effect = error
                page = self.detail({"q": "climate", "page": 2}, status=status)
                self.assertIn(message, page)
                self.assertIn('href="/?q=climate&amp;page=2"', page)

    def test_http_failure_is_not_reported_as_missing_record(self):
        for status in (403, 429, 500):
            with self.subTest(status=status):
                response = requests.Response()
                response.status_code = status
                self.get.return_value = response
                page = self.detail(status=502)
                self.assertIn("Não foi possível consultar a API", page)
                self.assertNotIn("O registo não foi encontrado", page)

    def test_invalid_response_has_a_clear_message(self):
        for payload in (None, [], {}, {"message": "invalid"}):
            with self.subTest(payload=payload):
                self.get.return_value.json.return_value = payload
                self.assertIn("resposta inválida", self.detail(status=502))
        self.get.return_value.json.side_effect = ValueError("invalid JSON")
        self.assertIn("resposta inválida", self.detail(status=502))

    def test_untrusted_fields_and_urls_are_safe(self):
        self.record["metadata"].update({
            "title": '<img src=x onerror="alert(1)">',
            "description": '<script>danger()</script>&lt;img src=x&gt;<b>Texto</b>',
            "access_conditions": '<img src=x><script>danger()</script>Condições',
            "creators": [{"name": "<script>author</script>", "url": "javascript:alert(2)"}],
            "license": {"id": "<script>license</script>", "url": "data:text/html,unsafe"},
            "related_identifiers": [{"identifier": "javascript:alert(3)"}],
        })
        self.record["files"][0]["links"]["self"] = "javascript:alert(4)"
        self.record["links"]["self_html"] = "javascript:alert(5)"
        self.record["doi_url"] = "javascript:alert(6)"
        page = self.detail()
        for unsafe in ("<img", "<script", "<b>Texto</b>", "danger()", 'href="javascript:', 'href="data:'):
            with self.subTest(unsafe=unsafe):
                self.assertNotIn(unsafe, page)
        self.assertIn("&lt;img", page)

    def test_only_valid_explicit_http_destinations_are_accepted(self):
        for url in (None, 123, "//example.org", "javascript:alert(1)",
                    "https://user:password@example.org", "https://example.org:invalid",
                    "https://[invalid", "https://example.org/\nunsafe"):
            with self.subTest(url=url):
                self.assertIsNone(safe_url(url))


if __name__ == "__main__":
    unittest.main()
