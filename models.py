"""Modelo comum. None indica informação ausente/inválida; vazios são conservados."""

from dataclasses import dataclass, field
from typing import Optional

DESCRIPTION_LIMIT = 300


@dataclass
class Author:
    name: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    url: Optional[str] = None


@dataclass
class License:
    identifier: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


@dataclass
class DataFile:
    name: Optional[str] = None
    format: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None


@dataclass
class RelatedResource:
    identifier: Optional[str] = None
    relation: Optional[str] = None
    resource_type: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Dataset:
    source: Optional[str] = None
    identifier: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    authors: Optional[list[Author]] = None
    doi: Optional[str] = None
    doi_url: Optional[str] = None
    publication_date: Optional[str] = None
    updated: Optional[str] = None
    keywords: Optional[list[str]] = None
    license: Optional[License] = None
    files: Optional[list[DataFile]] = None
    access_right: Optional[str] = None
    access_conditions: Optional[str] = None
    embargo_date: Optional[str] = None
    related_resources: Optional[list[RelatedResource]] = None

    @property
    def short_description(self):
        if self.description is None or len(self.description) <= DESCRIPTION_LIMIT:
            return self.description
        return self.description[:DESCRIPTION_LIMIT - 1].rstrip() + "…"


@dataclass
class SearchPage:
    results: list[Dataset] = field(default_factory=list)
    page: int = 1
    total: Optional[int] = None
    total_is_exact: bool = False
    previous_page: Optional[int] = None
    next_page: Optional[int] = None
