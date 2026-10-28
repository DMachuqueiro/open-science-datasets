from flask import Flask, render_template, request

from models import SearchPage
from zenodo import ZenodoError, get_dataset, search_datasets

app = Flask(__name__)


def _page_number(value):
    try:
        page = int(value)
        return page if page > 0 else 1
    except (TypeError, ValueError):
        return 1


@app.get("/")
def index():
    query = request.args.get("q", "").strip()
    page = _page_number(request.args.get("page", "1"))
    search = SearchPage(page=page)
    error = None
    if query:
        try:
            search = search_datasets(query, page)
        except ZenodoError as exc:
            error = str(exc)
    return render_template("index.html", query=query, search=search, error=error)


@app.get("/datasets/zenodo/<identifier>")
def dataset_detail(identifier):
    query = request.args.get("q", "").strip()
    page = _page_number(request.args.get("page", "1"))
    dataset = None
    error = None
    status = 200
    try:
        dataset = get_dataset(identifier)
    except ZenodoError as exc:
        error = str(exc)
        status = exc.status_code
    template = "_detail_content.html" if request.headers.get("X-Requested-With") == "fetch" else "detail.html"
    return render_template(
        template, dataset=dataset, error=error, query=query, page=page,
    ), status


if __name__ == "__main__":
    app.run()
