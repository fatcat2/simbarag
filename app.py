import os

from flask import Flask, request, jsonify, render_template, send_from_directory

from main import consult_simba_oracle

app = Flask(__name__, static_folder="raggr-frontend/dist/static", template_folder="raggr-frontend/dist")


# Serve React static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# Serve the React app for all routes (catch-all)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.template_folder, path)):
        return send_from_directory(app.template_folder, path)
    return render_template('index.html')

@app.route("/api/query", methods=["POST"])
def query():
    data  = request.get_json()
    query = data.get("query")
    return jsonify({"response": consult_simba_oracle(query)})

@app.route("/api/ingest", methods=["POST"])
def webhook():
    data = request.get_json()
    print(data)
    return jsonify({"status": "received"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

