from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import os
import tempfile
from fpdf import FPDF

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/generate_will", methods=["POST"])
def generate_will():
    data = request.json
    name = data.get("name")
    age = data.get("age")
    assets = data.get("assets", [])
    beneficiaries = data.get("beneficiaries", {})

    assets_text = ", ".join(assets)
    people_text = ", ".join([f"{k} ({v})" for k, v in beneficiaries.items()])

    prompt = f"""
    Du bist ein erfahrener juristischer Berater. Erstelle ein einfaches, deutschsprachiges Testament für:
    Name: {name}, Alter: {age}
    Digitale Güter: {assets_text}
    Begünstigte: {people_text}
    Das Testament soll juristisch korrekt und verständlich sein.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        will_text = response.choices[0].message.content

        # PDF erstellen
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in will_text.split('\n'):
            pdf.multi_cell(0, 10, line)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)

        return send_file(tmp.name, as_attachment=True, download_name="EchoVault_Testament.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return "✅ Echo Vault Server läuft."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
