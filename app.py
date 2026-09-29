from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from core import calculate_days, get_month_sha, get_options, get_year_sha


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/options")
def options():
    return jsonify(get_options())


@app.get("/api/year-sha")
def year_sha():
    try:
        return jsonify(get_year_sha(int(request.args.get("year", "2026")), int(request.args.get("mountain_id", "1"))))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/month-sha")
def month_sha():
    try:
        return jsonify(get_month_sha(int(request.args.get("year", "2026")),
                                     request.args.get("month", "丙申")))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/calculate")
def calculate():
    try:
        payload = request.get_json(force=True) or {}
        return jsonify(calculate_days(payload))
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("calculation failed")
        return jsonify({"error": f"计算失败：{exc}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
