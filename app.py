
from flask import Flask, render_template, request, send_file, jsonify, redirect, session
from openai import OpenAI
from fpdf import FPDF
import os
import tempfile

app = Flask(__name__)
app.secret_key = "doneo_@secure_3829kdhsA9nW2L"  # <- dein generierter Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/avatar")
@app.route("/unlock_free", methods=["POST"])
def unlock_free():
    session["free_unlocked"] = True
    return redirect("/formular")  # Passe ggf. an deine Eingabe-Seite an

def home():
    return render_template("avatar.html")

@app.route("/generate_vault", methods=["POST"])
def generate_vault():
        if not session.get("free_unlocked"):
        return "❌ Zugriff verweigert – bitte zuerst Zugang aktivieren", 403

    name = request.form.get("name")
    assets = request.form.get("assets")
    beneficiaries_raw = request.form.get("beneficiaries")
    message = request.form.get("message")
    identity = request.form.get("identity")

    beneficiaries = {}
    for pair in beneficiaries_raw.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            beneficiaries[k.strip()] = v.strip()

    people_text = ", ".join([f"{k} ({v})" for k, v in beneficiaries.items()])

    will_prompt = f"Du bist ein erfahrener juristischer Berater. Erstelle ein einfaches, deutschsprachiges Testament für: Name: {name}, Digitale Güter: {assets}, Begünstigte: {people_text}"
    letter_prompt = f"Schreibe einen würdevollen, persönlichen Abschiedsbrief von {name} an seine Hinterbliebenen: {message}"
    avatar_notice = f"Diese Person hat folgende Persönlichkeitsbeschreibung hinterlassen: {identity}. Mithilfe dieser Angaben kann Echo Vault eine KI-gestützte Antwort im Stil dieser Person simulieren."

    try:
        will_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": will_prompt}]
        )
        letter_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": letter_prompt}]
        )

        will_text = will_response.choices[0].message.content.strip()
        letter_text = letter_response.choices[0].message.content.strip()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"Digitales Testament für: {name}")
        pdf.multi_cell(0, 10, will_text)

        pdf.add_page()
        pdf.multi_cell(0, 10, f"Letzte persönliche Nachricht von {name}")
        pdf.multi_cell(0, 10, letter_text)

        pdf.add_page()
        pdf.multi_cell(0, 10, "Hinweis für Angehörige:")
        pdf.multi_cell(0, 10, avatar_notice)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)

        return send_file(tmp.name, as_attachment=True, download_name="EchoVault_Digitales_Vermächtnis.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
