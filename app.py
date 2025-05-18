from flask import Flask, request, jsonify, send_file, render_template
from openai import OpenAI
import os
import tempfile
from fpdf import FPDF

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

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
    Was möchten Sie hinterlassen: {assets_text}
    Empfänger: {people_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        will_text = response.choices[0].message.content

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

@app.route("/last_message", methods=["POST"])
def last_message():
    data = request.json
    name = data.get("name")
    message = data.get("message")

    prompt = f"""
    Schreibe einen würdevollen Abschiedsbrief von {name} auf Basis dieser Nachricht:

    {message}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        final_letter = response.choices[0].message.content

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in final_letter.split('\n'):
            pdf.multi_cell(0, 10, line)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)

        return send_file(tmp.name, as_attachment=True, download_name="Letzte_Nachricht_EchoVault.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/avatar_chat", methods=["POST"])
def avatar_chat():
    data = request.json
    base_identity = data.get("identity")
    message = data.get("message")

    system_prompt = f"""
    Du bist der digitale Avatar eines verstorbenen Menschen.
    Du antwortest so, wie diese Person zu Lebzeiten gesprochen hat.
    Hier ist ihre Persönlichkeit: {base_identity}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/vault", methods=["POST"])
def vault():
    data = request.json
    name = data.get("name")
    content = data.get("content")

    prompt = f"""
    Formuliere eine strukturierte, professionelle Übergabedokumentation für folgende vertrauliche Daten von {name}:

    {content}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in result.split('\n'):
            pdf.multi_cell(0, 10, line)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)

        return send_file(tmp.name, as_attachment=True, download_name="Vault_Übergabe_EchoVault.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
