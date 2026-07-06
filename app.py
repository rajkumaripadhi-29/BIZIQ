import os
import json
import uuid
import pickle
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename

from utils.data_processor import load_dataset, clean_data, detect_columns, get_preview, compute_column_info
from utils.visualizer import generate_charts, generate_custom_chart
from utils.insights import generate_insights

app = Flask(__name__)
app.secret_key = "biz-analytics-secret-2024"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024   # 50 MB


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return render_template("index.html", error="No file part in the request.")

    file = request.files["file"]
    if file.filename == "":
        return render_template("index.html", error="Please select a file before uploading.")

    if not allowed_file(file.filename):
        return render_template("index.html", error="Unsupported file type. Please upload a CSV or Excel file.")

    # Save file with a unique name to avoid collisions
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(filepath)

    try:
        # Load & clean
        df = load_dataset(filepath)
        df = clean_data(df)
        col_types = detect_columns(df)

        # Generate outputs
        charts   = generate_charts(df, col_types)
        insights = generate_insights(df, col_types)
        preview  = get_preview(df)
        col_info = compute_column_info(df)

        # Convert col_types lists to plain Python lists (datetime cols may have Timestamp keys)
        col_types_safe = {
            "numeric":     col_types["numeric"],
            "categorical": col_types["categorical"],
            "datetime":    col_types["datetime"],
        }

        # Persist cleaned dataframe for later custom-chart requests
        data_id = uuid.uuid4().hex
        data_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{data_id}.pkl")
        df.to_pickle(data_path)
        session["data_path"] = data_path
        session["col_types"] = col_types_safe

        # All column names for the dropdown menus
        all_columns = list(df.columns)

        return render_template(
            "dashboard.html",
            filename=file.filename,
            shape=df.shape,
            preview=preview,
            col_info=col_info,
            col_types=col_types_safe,
            charts=charts,
            insights=insights,
            all_columns=all_columns,
        )

    except Exception as e:
        return render_template("index.html", error=f"Error processing file: {str(e)}")
    finally:
        # Clean up the raw uploaded file (NOT the persisted pickle)
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/generate_custom_chart", methods=["POST"])
def custom_chart():
    """API endpoint: accept x_col, y_col, chart_type and return chart JSON."""
    data_path = session.get("data_path")
    if not data_path or not os.path.exists(data_path):
        return jsonify({"error": "Session expired. Please re-upload your file."}), 400

    payload = request.get_json(force=True)
    x_col      = payload.get("x_col", "").strip()
    y_col      = payload.get("y_col", "").strip()
    chart_type = payload.get("chart_type", "bar").strip()

    if not x_col or not y_col:
        return jsonify({"error": "Both X-axis and Y-axis columns are required."}), 400

    if x_col == y_col:
        return jsonify({"error": "Please make sure the two selected columns are different."}), 400

    try:
        df = pd.read_pickle(data_path)
        if x_col not in df.columns or y_col not in df.columns:
            return jsonify({"error": "Selected column not found in dataset."}), 400

        chart = generate_custom_chart(df, x_col, y_col, chart_type)
        return jsonify({"chart": chart})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
