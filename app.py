
import os
import stripe
import datetime
from flask import Flask, render_template, request, send_file, session, redirect, jsonify
from openai import OpenAI
from fpdf import FPDF
import tempfile

# Initialisierung
app = Flask(__name__)
app.secret_key = "doneo_@secure_3829kdhsA9nW2L"
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Admin- und Nutzungsfunktionen
def is_access_granted():
    return any([
        session.get("free_unlocked"),
        session.get("plus_unlocked"),
        session.get("pro_unlocked")
    ])
@app.route("/")
def landing():
    return render_template("index.html")
    
@app.route("/formular")
def formular():
    typ = request.args.get("typ", "")
    return render_template("echo_vault_final_template.html", typ=typ)



@app.route("/status")
def status():
    return {
        "free": session.get("free_unlocked", False),
        "plus": session.get("plus_unlocked", False),
        "pro": session.get("pro_unlocked", False),
        "downloads_left": session.get("downloads_left", "∞"),
        "last_access": session.get("last_access", "nie"),
    }

@app.route("/logout")
def logout():
    session.clear()
    return "✅ Du wurdest abgemeldet. Deine Sitzung ist beendet."

@app.before_request
def track_pdf_usage():
    if request.path == "/generate_vault" and request.method == "POST":
        if session.get("free_unlocked") and not session.get("pro_unlocked") and not session.get("plus_unlocked"):
            if session.get("downloads_left") is None:
                session["downloads_left"] = 1
            if session["downloads_left"] <= 0:
                return "❌ Du hast dein Free-Limit erreicht. Bitte upgraden.", 403
            session["downloads_left"] -= 1
            session["last_access"] = str(datetime.datetime.now())

# Tarifauswahl
@app.route("/select")
def select_plan():
    return render_template("select_plan.html")

@app.route("/unlock_free", methods=["POST"])
def unlock_free():
    session["free_unlocked"] = True
    return redirect("/formular")

# Stripe Checkout
@app.route("/checkout/<plan>")
def checkout(plan):
    prices = {
        "pro": "price_1RPylqQjaqheqwMhHEWyGqDP",
        "plus": "price_1RPymFQjaqheqwMhhN76SYLw",
        "free": "price_1RPyw7QjaqheqwMhA6Mfg6OH"
    }

    if plan not in prices:
        return "Ungültiger Tarif", 400

    try:
        session_data = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": prices[plan], "quantity": 1}],
            mode="payment",
            success_url="https://echo-vault.onrender.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://echo-vault.onrender.com/cancel"
        )
        return redirect(session_data.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/success")
def success():
    session_id = request.args.get("session_id")
    if not session_id:
        return "Keine Session-ID", 400
    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        price_id = stripe_session["display_items"][0]["price"]["id"]
        if price_id == "price_1RPylqQjaqheqwMhHEWyGqDP":
            session["pro_unlocked"] = True
        elif price_id == "price_1RPymFQjaqheqwMhhN76SYLw":
            session["plus_unlocked"] = True
        elif price_id == "price_1RPyw7QjaqheqwMhA6Mfg6OH":
            session["free_unlocked"] = True
        return render_template("success.html")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/cancel")
def cancel():
    return "❌ Zahlung abgebrochen."



# PDF-Generierung
@app.route("/generate_vault", methods=["POST"])
def generate_vault():
    if not is_access_granted():
        return "❌ Zugriff verweigert – bitte zuerst Zugang aktivieren", 403

from flask import request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from fpdf import FPDF
import os
import tempfile

@app.route("/submit_form", methods=["POST"])
def submit_form():
    name = request.form.get("name", "Unbekannt")
    message = request.form.get("message", "")
    identity = request.form.get("identity", "")
    typ = request.form.get("typ", "Echo Vault")
    uploaded_files = request.files.getlist("file")

    # Erstelle temporäres PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.multi_cell(0, 10, f"{typ}\n\nVon: {name}\n\nNachricht:\n{message}\n\nCharakterbeschreibung:\n{identity}")

    # Speicherort für Dateien
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "EchoVault_Dokument.pdf")
    pdf.output(pdf_path)

    # Optional: Speichere hochgeladene Dateien
    for file in uploaded_files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(temp_dir, filename))

    # OPTIONAL: KI-Stimme vorbereiten (Platzhalter)
    # Hier könntest du später ElevenLabs oder andere APIs ansprechen
    # Audio-Datei könnte ebenfalls im PDF referenziert oder verlinkt werden

    return send_file(pdf_path, as_attachment=True, download_name="EchoVault_Dokument.pdf")

    name = request.form.get("name")
    assets = request.form.get("assets")
    beneficiaries = request.form.get("beneficiaries")
    message = request.form.get("message")
    identity = request.form.get("identity")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Echo Vault – Digitales Vermächtnis", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Name: {name}")
    pdf.multi_cell(0, 10, f"Hinterlassene Inhalte:{assets}")
    pdf.multi_cell(0, 10, f"Empfänger:{beneficiaries}")
    pdf.multi_cell(0, 10, f"Letzte Nachricht:{message}")
    pdf.multi_cell(0, 10, f"Persönlichkeitsbeschreibung:{identity}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        pdf.output(temp.name)
        return send_file(temp.name, as_attachment=True, download_name="EchoVault.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

