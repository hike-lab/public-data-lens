"""§7 정본 URI 디레퍼런싱 — service.datahub.kr/projects/public-data-lens/... 경로가 정본 표현으로 해소되는지 검증.

JSON-LD 문서의 @id가 약속한 그대로 접속 가능해야 재개봉 없이 Cool URIs를 지킬 수 있다.
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from datanav.api.rest import app
from datanav.config import BASE_URI
from datanav.spec import SPEC_VERSION
from tests.conftest import requires_catalog

client = TestClient(app)
CANON = "/projects/public-data-lens"


def test_context_resolves_as_jsonld():
    r = client.get(f"{CANON}/context/catalog/1.0")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/ld+json")
    assert "@context" in r.json()


def test_rules_and_spec_resolve():
    rules = client.get(f"{CANON}/rules/catalog/1.0")
    assert rules.status_code == 200 and "rules" in rules.json()
    spec = client.get(f"{CANON}/spec/tools/1.0")
    assert spec.status_code == 200 and spec.json()["specVersion"] == SPEC_VERSION


def test_shapes_and_prompt_media_types():
    shapes = client.get(f"{CANON}/shapes/catalog/1.0")
    assert shapes.status_code == 200
    assert shapes.headers["content-type"].startswith("text/turtle")
    assert "sh:" in shapes.text
    prompt = client.get(f"{CANON}/prompts/build-data-plan/1.0")
    assert prompt.status_code == 200
    assert prompt.headers["content-type"].startswith("text/markdown")


@requires_catalog
def test_dataset_uri_resolves_to_canonical_doc(service):
    key = service.search_datasets(page_size=1)["data"]["items"][0]["listKey"]
    r = client.get(f"{CANON}/dataset/{key}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/ld+json")
    doc = r.json()
    assert doc["@id"] == f"{BASE_URI}/dataset/{key}"  # @id = 접속한 URI (Cool URIs)
    assert doc["@type"] == "dcat:Dataset"


def test_catalog_record_uri_resolves_to_canonical_doc(monkeypatch, catalog_service):
    from datanav.api import rest

    monkeypatch.setattr(rest, "_svc", lambda: catalog_service)
    dataset = catalog_service.get_dataset("rec-001", "jsonld")["data"]["dataset"]
    path = dataset["kdp:catalogRecord"].replace("https://service.datahub.kr", "")
    r = client.get(path)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/ld+json")
    doc = r.json()
    assert doc["@context"]
    assert doc["@id"] == dataset["kdp:catalogRecord"]
    assert doc["@type"] == "dcat:CatalogRecord"
    assert doc["foaf:primaryTopic"]["@id"] == f"{BASE_URI}/dataset/list-001"


def test_catalog_record_not_found_returns_error_envelope(monkeypatch, catalog_service):
    from datanav.api import rest

    monkeypatch.setattr(rest, "_svc", lambda: catalog_service)
    r = client.get(f"{CANON}/catalog/{catalog_service.snapshot}/record/no-such-record")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DATASET_NOT_FOUND"


def test_catalog_record_unknown_snapshot(monkeypatch, catalog_service):
    from datanav.api import rest

    monkeypatch.setattr(rest, "_svc", lambda: catalog_service)
    r = client.get(f"{CANON}/catalog/1999-01/record/rec-001")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "SNAPSHOT_NOT_FOUND"


@requires_catalog
def test_dataset_html_redirects_to_portal(service):
    key = service.search_datasets(page_size=1)["data"]["items"][0]["listKey"]
    r = client.get(f"{CANON}/dataset/{key}",
                   headers={"Accept": "text/html"}, follow_redirects=False)
    assert r.status_code == 303
    assert "data.go.kr" in r.headers["location"]


@requires_catalog
def test_dataset_not_found_returns_error_envelope():
    r = client.get(f"{CANON}/dataset/00000000없음")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DATASET_NOT_FOUND"


@requires_catalog
def test_catalog_current_and_snapshot(service):
    r = client.get(f"{CANON}/catalog/current")
    assert r.status_code == 200
    assert r.json()["@type"] == "dcat:Catalog"
    same = client.get(f"{CANON}/catalog/{service.snapshot}")
    assert same.status_code == 200
    other = client.get(f"{CANON}/catalog/1999-01")
    assert other.status_code == 404
    assert other.json()["error"]["code"] == "SNAPSHOT_NOT_FOUND"


@requires_catalog
def test_bulk_files_served_and_traversal_blocked(service):
    fname = f"datasets-{service.snapshot}.ndjson.gz"
    r = client.get(f"{CANON}/catalog/current/files/{fname}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/gzip"
    bad = client.get(f"{CANON}/catalog/current/files/..%2Fcurrent.json")
    assert bad.status_code in (404, 400)
    db = client.get(f"{CANON}/catalog/current/files/catalog.db")
    assert db.status_code == 404  # 허용 확장자 아님


@requires_catalog
def test_aird_assessment_resolves(service):
    r = client.get(f"{CANON}/catalog/current/aird-assessment")
    assert r.status_code == 200
    doc = r.json()
    assert doc["@type"] == "kdp:AirdAssessment"
    assert "aird:qualityIndexMMI" in json.dumps(doc)
