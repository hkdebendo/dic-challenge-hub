from flask import Flask, jsonify, request, Response

app = Flask(__name__)


@app.get("/")
def index():
    return """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nova Portal</title>
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
  <main class="portal">
    <p class="eyebrow">Nova Systems</p>
    <h1>Bienvenue sur Nova Portal.</h1>
    <p>Aucun document public disponible.</p>
  </main>
</body>
</html>
"""


@app.get("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /old-panel/\n", mimetype="text/plain")


@app.get("/old-panel/")
def old_panel():
    return """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Old Panel</title>
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
  <main class="portal">
    <p class="eyebrow">Legacy</p>
    <h1>Ancien panneau</h1>
    <p>Aucun rapport charge.</p>
  </main>
  <script src="/assets/legacy.js"></script>
</body>
</html>
"""


@app.get("/assets/legacy.js")
def legacy_js():
    return Response('const reportEndpoint = "/api/report?id=12";\n', mimetype="application/javascript")


@app.get("/assets/style.css")
def style_css():
    return Response(
        """
body {
  background: #111827;
  color: #f8fafc;
  font: 16px/1.5 "Segoe UI", system-ui, sans-serif;
  margin: 0;
}
.portal {
  margin: 12vh auto;
  max-width: 720px;
  padding: 32px;
}
.eyebrow {
  color: #4ade80;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}
h1 {
  font-size: clamp(36px, 7vw, 76px);
  line-height: 1;
  margin: 0 0 18px;
}
p {
  color: #cbd5e1;
}
""",
        mimetype="text/css",
    )


@app.get("/api/report")
def report():
    report_id = request.args.get("id", "")
    if report_id == "12":
        return jsonify({"id": 12, "title": "Rapport public", "content": "Aucune anomalie."})
    if report_id == "47":
        return jsonify(
            {
                "id": 47,
                "title": "Rapport d'incident",
                "flag": "DIC{un_identifiant_ne_remplace_pas_une_autorisation}",
            }
        )
    return jsonify({"error": "rapport introuvable"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
