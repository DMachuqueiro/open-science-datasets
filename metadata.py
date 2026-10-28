"""Converte metadados do Zenodo para o modelo comum; não realiza pedidos HTTP."""

from html.parser import HTMLParser
from urllib.parse import urlsplit

from models import Author, DataFile, Dataset, License, RelatedResource


def as_dict(value):
    return value if isinstance(value, dict) else {}


def text(value):
    return value.strip() if isinstance(value, str) else None


def _first_text(*values):
    return next((text(value) for value in values if isinstance(value, str)), None)


def record_identifier(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    value = str(value)
    if value.isascii() and value.isdecimal() and len(value) <= 20 and int(value) > 0:
        return value
    return None


def safe_url(value):
    """Aceita apenas destinos HTTP(S) explícitos e sem credenciais."""
    value = text(value)
    if not value or any(char.isspace() or ord(char) < 32 for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme in {"https", "http"} and parsed.hostname
                and parsed.username is None and parsed.password is None):
            parsed.port  # Valida também portas malformadas.
            return value
    except ValueError:
        pass
    return None


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1
        self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value):
    if not isinstance(value, str):
        return None
    parser = _TextParser()
    parser.feed(value)
    parser.close()
    return " ".join("".join(parser.parts).split())


def _collection(value, normalize):
    if not isinstance(value, list):
        return None
    return [normalize(item) for item in value if isinstance(item, dict)]


def _original_url(record):
    links = as_dict(record.get("links"))
    for key in ("self_html", "html"):
        url = safe_url(links.get(key))
        if url:
            parsed = urlsplit(url)
            if (parsed.scheme == "https" and parsed.netloc == "zenodo.org"
                    and parsed.path.startswith(("/records/", "/record/"))):
                return url
    identifier = record_identifier(record.get("id"))
    return f"https://zenodo.org/records/{identifier}" if identifier else None


def _author(item):
    return Author(
        name=text(item.get("name")),
        affiliation=text(item.get("affiliation")),
        orcid=text(item.get("orcid")),
        url=safe_url(item.get("url")) or safe_url(item.get("orcid")),
    )


def _file(item):
    size = item.get("size")
    return DataFile(
        name=_first_text(item.get("key"), item.get("filename")),
        format=_first_text(item.get("mimetype"), item.get("type")),
        size=size if type(size) is int and size >= 0 else None,
        url=safe_url(as_dict(item.get("links")).get("download"))
            or safe_url(as_dict(item.get("links")).get("self")),
    )


def _related(item):
    identifier = text(item.get("identifier"))
    return RelatedResource(
        identifier=identifier,
        relation=text(item.get("relation")),
        resource_type=text(item.get("resource_type")),
        url=safe_url(item.get("url")) or safe_url(identifier),
    )


def normalize_zenodo_record(record):
    metadata = as_dict(record.get("metadata"))
    raw_license = metadata.get("license")
    license_data = None
    if isinstance(raw_license, dict):
        license_data = License(
            identifier=text(raw_license.get("id")),
            name=text(raw_license.get("title")),
            url=safe_url(raw_license.get("url")),
        )
    elif isinstance(raw_license, str):
        license_data = License(identifier=text(raw_license))

    keywords = metadata.get("keywords")
    return Dataset(
        source="Zenodo",
        identifier=record_identifier(record.get("id")),
        title=text(metadata.get("title")),
        description=plain_text(metadata.get("description")),
        url=_original_url(record),
        authors=_collection(metadata.get("creators"), _author),
        doi=_first_text(metadata.get("doi"), record.get("doi")),
        doi_url=safe_url(record.get("doi_url"))
            or safe_url(as_dict(record.get("links")).get("doi")),
        publication_date=text(metadata.get("publication_date")),
        updated=_first_text(record.get("updated"), record.get("modified")),
        keywords=[item.strip() for item in keywords if isinstance(item, str)]
            if isinstance(keywords, list) else None,
        license=license_data,
        files=_collection(record.get("files"), _file),
        access_right=text(metadata.get("access_right")),
        access_conditions=plain_text(metadata.get("access_conditions")),
        embargo_date=text(metadata.get("embargo_date")),
        related_resources=_collection(metadata.get("related_identifiers"), _related),
    )
