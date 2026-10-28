"""Testes isolados: as respostas simuladas nunca são usadas pela aplicação."""

import unittest
from unittest.mock import Mock, patch

import requests

from app import app
from models import DESCRIPTION_LIMIT
from zenodo import API_URL, REQUEST_TIMEOUT, search_datasets


class SearchTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        patcher = patch("zenodo.requests.get")
        self.get = patcher.start()
        self.addCleanup(patcher.stop)

    def respond_with(self, hits):
        self.get.return_value = Mock()
        self.get.return_value.json.return_value = {"hits": {"hits": hits}}

    def page(self, query="climate"):
        response = self.client.get("/", query_string={"q": query})
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_initial_and_empty_searches_do_not_call_api(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        for query in ("", "   ", "\t\n"):
            with self.subTest(query=query):
                self.assertIn("Introduz palavras-chave", self.page(query))
                self.assertEqual(search_datasets(query).results, [])
        self.get.assert_not_called()

    def test_search_uses_user_query_dataset_filter_and_limit(self):
        self.respond_with([{
            "metadata": {"title": "Dataset de teste", "description": "<p>Dados &amp; clima.</p>"},
            "links": {"html": "https://zenodo.org/records/123"},
        }])
        query = "clima & oceanos + açores"
        page = self.page(f"  {query}  ")
        self.get.assert_called_once_with(
            API_URL,
            params={"q": query, "type": "dataset", "size": 20, "page": 1},
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        self.get.return_value.raise_for_status.assert_called_once_with()
        self.assertIn("Dataset de teste", page)
        self.assertIn("Dados &amp; clima.", page)
        self.assertNotIn('href="https://zenodo.org/records/123"', page)

    def test_never_displays_more_than_twenty_results(self):
        self.respond_with([{"id": i, "metadata": {"title": f"Dataset {i}"}} for i in range(1, 26)])
        page = self.page()
        self.assertEqual(page.count("<article>"), 20)
        self.assertNotIn("Dataset 21", page)

    def test_missing_and_null_fields_have_explicit_fallbacks(self):
        self.respond_with([{}, {"metadata": None, "links": None}, {
            "metadata": {"title": None, "description": None},
        }])
        page = self.page()
        self.assertEqual(page.count("Título não disponível."), 3)
        self.assertEqual(page.count("Descrição não disponível."), 3)
        self.assertNotIn("Ligação para o registo original não disponível.", page)

    def test_unexpected_field_types_do_not_crash(self):
        self.respond_with([{"metadata": {"title": [], "description": {}}, "links": []}])
        self.assertIn("Descrição não disponível.", self.page())

    def test_record_id_is_used_when_link_is_missing(self):
        self.respond_with([{"id": 123}, {"id": "456"}])
        results = search_datasets("climate").results
        self.assertEqual([item.url for item in results], [
            "https://zenodo.org/records/123", "https://zenodo.org/records/456",
        ])

    def test_self_html_link_is_supported(self):
        self.respond_with([{"links": {"self_html": "https://zenodo.org/records/123"}}])
        self.assertEqual(search_datasets("climate").results[0].url, "https://zenodo.org/records/123")

    def test_empty_results_have_a_clear_message(self):
        self.respond_with([])
        self.assertIn("Não foram encontrados datasets", self.page())

    def test_timeout_is_distinct_from_no_results(self):
        self.get.side_effect = requests.Timeout()
        page = self.page()
        self.assertIn("demorou demasiado tempo", page)
        self.assertIn('role="alert"', page)
        self.assertNotIn("Não foram encontrados", page)

    def test_connection_failure_is_distinct_from_no_results(self):
        self.get.side_effect = requests.ConnectionError()
        page = self.page()
        self.assertIn("Não foi possível consultar a API", page)
        self.assertNotIn("Não foram encontrados", page)

    def test_http_errors_have_a_clear_message(self):
        for status in (400, 403, 429, 500, 503):
            with self.subTest(status=status):
                response = requests.Response()
                response.status_code = status
                self.get.return_value = response
                page = self.page()
                self.assertIn("Não foi possível consultar a API", page)
                self.assertNotIn("Não foram encontrados", page)

    def test_invalid_json_has_a_clear_message(self):
        self.get.return_value.json.side_effect = ValueError("invalid JSON")
        self.assertIn("resposta inválida", self.page())

    def test_invalid_response_structure_is_not_presented_as_no_results(self):
        for payload in (None, [], {}, {"hits": None}, {"hits": {"hits": None}},
                        {"hits": {"hits": [None]}}):
            with self.subTest(payload=payload):
                self.get.return_value.json.return_value = payload
                page = self.page()
                self.assertIn("resposta inválida", page)
                self.assertNotIn("Não foram encontrados", page)

    def test_description_is_plain_text_and_short(self):
        self.respond_with([{"metadata": {
            "description": "<p>Primeiro</p><p>Segundo &amp; terceiro</p>"
                           "<script>alert('unsafe')</script><style>body{}</style>"
                           + " texto" * 100,
        }}])
        description = search_datasets("climate").results[0].short_description
        self.assertTrue(description.startswith("Primeiro Segundo & terceiro"))
        self.assertNotIn("<p>", description)
        self.assertNotIn("alert", description)
        self.assertNotIn("body", description)
        self.assertEqual(len(description), DESCRIPTION_LIMIT)
        self.assertTrue(description.endswith("…"))

    def test_untrusted_text_and_links_are_safe(self):
        self.respond_with([{
            "metadata": {
                "title": '<img src=x onerror="alert(1)">',
                "description": '&lt;img src=x onerror="alert(2)"&gt;<b>Texto</b>',
            },
            "links": {"html": "javascript:alert(3)"},
        }])
        page = self.page('<script>alert(4)</script>')
        self.assertNotIn("<img", page)
        self.assertNotIn("<script>alert(4)</script>", page)
        self.assertNotIn("<b>Texto</b>", page)
        self.assertNotIn("javascript:", page)
        self.assertIn("&lt;img", page)
        self.assertNotIn("Ligação para o registo original não disponível.", page)

    def test_pagination_preserves_query_and_uses_one_api_request(self):
        self.respond_with([{"id": 123, "metadata": {"title": "Dataset"}}])
        self.get.return_value.json.return_value.update({"links": {
            "prev": API_URL + "?page=1", "next": API_URL + "?page=3",
        }})
        self.get.return_value.json.return_value["hits"]["total"] = 65
        response = self.client.get("/", query_string={"q": "clima & oceanos", "page": "2"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.get.assert_called_once_with(
            API_URL, params={"q": "clima & oceanos", "type": "dataset", "size": 20, "page": 2},
            headers={"Accept": "application/json"}, timeout=REQUEST_TIMEOUT,
        )
        self.assertIn('aria-current="page">Página 2', page)
        self.assertIn('rel="prev" href="/?q=clima+%26+oceanos&amp;page=1"', page)
        self.assertIn('rel="next" href="/?q=clima+%26+oceanos&amp;page=3"', page)
        self.assertIn('/datasets/zenodo/123?q=clima+%26+oceanos&amp;page=2', page)
        self.assertIn("65 resultados indicados", page)

    def test_invalid_page_parameters_fall_back_to_first_page(self):
        self.respond_with([])
        for value in ("", "abc", "0", "-2", "2.5", "9" * 5000):
            with self.subTest(value=value[:20]):
                self.get.reset_mock()
                response = self.client.get("/", query_string={"q": "climate", "page": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.get.call_args.kwargs["params"]["page"], 1)

    def test_empty_later_page_does_not_claim_entire_search_is_empty(self):
        self.respond_with([])
        response = self.client.get("/", query_string={"q": "climate", "page": "9"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Não existem resultados nesta página", page)
        self.assertIn('href="/?q=climate&amp;page=1"', page)
        self.assertNotIn("Não foram encontrados datasets", page)

    def test_exact_total_can_supply_navigation_when_links_are_absent(self):
        self.respond_with([{"id": 123}])
        self.get.return_value.json.return_value["hits"]["total"] = {"value": 41, "relation": "eq"}
        result = search_datasets("climate", 2)
        self.assertEqual((result.previous_page, result.next_page, result.total), (1, 3, 41))

    def test_api_links_take_precedence_over_totals(self):
        self.respond_with([{"id": 123}])
        self.get.return_value.json.return_value.update({"links": {}})
        self.get.return_value.json.return_value["hits"]["total"] = 100
        self.assertIsNone(search_datasets("climate").next_page)

    def test_unknown_or_lower_bound_total_does_not_invent_navigation(self):
        for total in (None, "100", -1, True, {"value": 100, "relation": "gte"},
                      {"value": 100, "relation": "unknown"}, {"value": 100, "relation": []}):
            with self.subTest(total=total):
                self.respond_with([{"id": 123}])
                self.get.return_value.json.return_value["hits"]["total"] = total
                result = search_datasets("climate")
                self.assertIsNone(result.next_page)
                self.assertFalse(result.total_is_exact)

    def test_pagination_links_do_not_redirect_to_untrusted_destinations(self):
        for url in ("https://example.org/api/records?page=2", "javascript:alert(1)",
                    API_URL + "?page=999", "https://zenodo.org/records?page=2"):
            with self.subTest(url=url):
                self.respond_with([{"id": 123}])
                self.get.return_value.json.return_value["links"] = {"next": url}
                self.assertIsNone(search_datasets("climate").next_page)

    def test_search_only_links_to_details_and_includes_accessible_dialog(self):
        self.respond_with([{"id": 123}])
        page = self.page()
        self.assertNotIn('href="https://zenodo.org/records/123"', page)
        self.assertNotIn(">Link</a>", page)
        self.assertIn('data-dataset-detail aria-haspopup="dialog"', page)
        self.assertIn('<dialog id="dataset-dialog" aria-label="Detalhes do dataset">', page)
        self.assertIn('href="/datasets/zenodo/123?q=climate&amp;page=1"', page)


if __name__ == "__main__":
    unittest.main()
