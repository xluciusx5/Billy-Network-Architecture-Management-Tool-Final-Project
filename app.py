import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from utils.processing import generate_network_diagram
#from utils.vulnerability import generate_vulnerability_report
from utils.vulnerability import predict_vulnerability_days
from datetime import datetime, timedelta
import re



app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flashing messages


UPLOAD_FOLDER = "datasets"
OUTPUT_FOLDER = "static/diagrams"
ALLOWED_EXTENSIONS = {"csv", "xlsx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_dataset(filepath):
    """Check if the uploaded dataset has the required structure."""
    try:
        df = pd.read_excel(filepath, engine='openpyxl') if filepath.endswith(".xlsx") else pd.read_csv(filepath)

        # Standardize column names (lowercase, no spaces)
        df.columns = df.columns.str.strip().str.lower()

        required_columns = ["hostname", "manufacturer", "model name", "end of life"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return f"Error: Missing required columns: {missing_columns}"

        return None  # No errors, dataset is valid
    except Exception as e:
        return f"Error: Could not process the file. {str(e)}"

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded!")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected!")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Validate dataset before processing
            validation_error = validate_dataset(filepath)
            if validation_error:
                flash(validation_error)
                os.remove(filepath)  # Delete the invalid file
                return redirect(request.url)

            # Generate Network Diagram
            diagram_filename = generate_network_diagram(filepath, app.config["OUTPUT_FOLDER"])
            return render_template("options.html", diagram=diagram_filename, filename=filename)
    
    return render_template("index.html")

@app.route("/report")
def equipment_report():
    """Generate and display the Equipment Report."""
    try:
        latest_file = max(os.listdir(app.config["UPLOAD_FOLDER"]), key=lambda f: os.path.getctime(os.path.join(app.config["UPLOAD_FOLDER"], f)))
        df = pd.read_excel(os.path.join(app.config["UPLOAD_FOLDER"], latest_file), engine='openpyxl') if latest_file.endswith(".xlsx") else pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"], latest_file))

        df.columns = df.columns.str.strip().str.lower()  # Standardize columns

        column_map = {
            "hostname": ["hostname", "device name", "host"],
            "manufacturer": ["manufacturer", "vendor", "brand"],
            "model name": ["model name", "model", "device model"],
            "end of life": ["end of life", "eol", "eol date"]
        }

        standardized_columns = {}
        for key, possible_names in column_map.items():
            for name in possible_names:
                if name in df.columns:
                    standardized_columns[key] = name
                    break

        for key in column_map.keys():
            if key not in standardized_columns:
                df[key] = "Unknown"
            else:
                df[key] = df[standardized_columns[key]]

        report_df = df[["hostname", "manufacturer", "model name", "end of life"]]
        report_html = report_df.to_html(classes="report-table", index=False)

        return render_template("report.html", table=report_html)
    except Exception as e:
        flash(f"Error generating report: {str(e)}")
        return redirect(url_for("upload_file"))
    
from utils.ssh_fortigate import fetch_firmware_from_fortigate
@app.route("/vulnerability")
def vulnerability_prediction():
    latest_file = max(
        os.listdir(app.config["UPLOAD_FOLDER"]),
        key=lambda f: os.path.getctime(os.path.join(app.config["UPLOAD_FOLDER"], f))
    )
    df = pd.read_excel(os.path.join(app.config["UPLOAD_FOLDER"], latest_file), engine='openpyxl') \
        if latest_file.endswith(".xlsx") else pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"], latest_file))

    # Filter only firewall/router devices based on hostname or model
    df_fw = df[df["Hostname"].str.contains(r"(FG|FW|RT|R01)", na=False)]

    # Mock CVE history
    cve_data = {
        "FG-81F": {"release_date": "2021-01-01", "vuln_date": "2022-04-15"},
        "FG-60F": {"release_date": "2020-08-01", "vuln_date": "2021-09-20"},
        "FGT_VM64": {"release_date": "2021-06-01", "vuln_date": "2022-12-01"},
        "FG-40F": {"release_date": "2020-04-01", "vuln_date": "2021-06-30"},
    }

    predictions = []

    for _, row in df_fw.iterrows():
        model = row.get("Model Name", "Unknown")
        hostname = row.get("Hostname", "Unknown")
        ip = row.get("External IP Address", "")
        firmware = row.get("Software Version", "Unknown")

        # Optional: If firmware is missing, mark it clearly
        if not firmware or str(firmware).strip().lower() in ["", "unknown", "nan"]:
            firmware = "Unknown"

        version_info = cve_data.get(model)
        if version_info:
            release = pd.to_datetime(version_info["release_date"])
            vuln = pd.to_datetime(version_info["vuln_date"])
            safe_days = (vuln - release).days
            predicted_vuln_date = release + pd.Timedelta(days=safe_days)

            # Assign risk level
            days_remaining = (predicted_vuln_date - pd.Timestamp.today()).days
            if days_remaining < 30:
                risk = "🔴 High"
            elif days_remaining < 90:
                risk = "🟠 Medium"
            else:
                risk = "🟢 Low"
        else:
            predicted_vuln_date = "Unknown"
            risk = "⚪ Unknown"

        predictions.append({
            "Hostname": hostname,
            "Model": model,
            "External IP": ip,
            "Firmware Version": firmware,
            "Predicted Vulnerability": predicted_vuln_date,
            "Risk Level": risk
        })

    return render_template("vulnerability.html", predictions=predictions)
   

@app.route("/diagrams/<path:filename>")
def view_diagram(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)


from utils.ssh_fortigate import fetch_firmware_from_fortigate
from utils.vulnerability import predict_vulnerability_days

@app.route("/fetch_firmware", methods=["GET", "POST"])
def fetch_firmware():
    firmware_result = None
    prediction_result = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Read dataset and extract the first FortiGate IP
        dataset_path = max(
            [os.path.join(app.config["UPLOAD_FOLDER"], f) for f in os.listdir(app.config["UPLOAD_FOLDER"])],
            key=os.path.getctime
        )
        df = pd.read_excel(dataset_path, engine='openpyxl') if dataset_path.endswith(".xlsx") else pd.read_csv(dataset_path)
        df.columns = df.columns.str.strip().str.lower()

        # Find the first Fortinet device
        fortigate_ip = None
        for _, row in df.iterrows():
            if "fortinet" in row.get("manufacturer", "").lower():
                fortigate_ip = row.get("external ip address")
                break

        if not fortigate_ip:
            flash("No FortiGate device found in the dataset.")
            return render_template("fetch_firmware.html")

        # SSH into device
        firmware_result = fetch_firmware_from_fortigate(fortigate_ip, username, password)

        # Extract firmware version 
        version_match = re.search(r"(v\d+\.\d+\.\d+)", firmware_result)
        clean_version = version_match.group(1) if version_match else "Unknown"

        # Load CVE dataset
        cve_df = pd.read_excel("../FortinetVulnerabilities.xlsx")
        cve_df.columns = cve_df.columns.str.lower().str.strip()

        # Attempt to find release date
        match = cve_df[cve_df["firmware version"] == clean_version]
        if not match.empty:
            release_date = match.iloc[0]["release date"]
        else:
            # 🔁 Fallback: hardcoded release dates
            manual_release_dates = {
                "v7.6.2": "2024-04-01",
                "v7.4.6": "2023-12-15",
                "v7.2.5": "2023-10-01"
            }
            release_date = manual_release_dates.get(clean_version)

        # Predict vulnerability if we have release date
        if release_date:
            try:
                predicted_days = predict_vulnerability_days(str(release_date))
                predicted_date = datetime.today() + timedelta(days=predicted_days)

                prediction_result = {
                    "firmware_version": clean_version,
                    "predicted_date": predicted_date.strftime("%Y-%m-%d"),
                    "days": predicted_days,
                    "risk": "🔴 High" if predicted_days < 90 else "🟠 Medium" if predicted_days < 180 else "🟢 Low"
                }
            except Exception as e:
                prediction_result = {
                    "firmware_version": clean_version,
                    "predicted_date": "Prediction failed",
                    "days": "Error",
                    "risk": "⚪ Error"
                }
        else:
            prediction_result = {
                "firmware_version": clean_version,
                "predicted_date": "Unknown",
                "days": "Unknown",
                "risk": "⚪ Unknown"
            }

    return render_template("fetch_firmware.html", firmware_result=firmware_result, prediction=prediction_result)







if __name__ == "__main__":
    app.run(debug=True)






