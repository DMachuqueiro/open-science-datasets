from flask import Flask, render_template, request

app = Flask(__name__)


@app.get("/")
def index():
    query = request.args.get("q", "").strip()
    return render_template("index.html", query=query)


if __name__ == "__main__":
    app.run()
