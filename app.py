import os
import stripe
import datetime
import tempfile
from flask import Flask, render_template, request, send_file, session, redirect, jsonify
from werkzeug.utils import secure_filename
from openai import OpenAI
from fpdf import FPDF

# Initialisierung
app = Flask(__name__)
app.secret_key = "doneo_@secure_3829kdhsA9nW2L"
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Routen
@app.route("/")
def index():
    return render_template("index.html")
    
@app.route("/formular")
def formular():
    return render_template("formular.html")
    
@app.route("/was-ist-echo-vault")
def was_ist_echo_vault():
    return render_template("was_ist_echo_vault.html")

@app.route("/beispiele")
def beispiele():
    return render_template("beispiele.html")

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/kontakt")
def kontakt():
    return render_template("kontakt.html")

@app.route("/nutzung")
def nutzung():
    return render_template("nutzung.html")

# Plan-Auswahl
@app.route("/select")
def select_plan():
    return render_template("select_plan.html")

@app.route("/unlock_free", methods=["POST"])
def unlock_free():
    session["free_unlocked"] = True
    return redirect("/formular")

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
        line_items = stripe.checkout.Session.list_line_items(session_id, limit=1)
        price_id = line_items.data[0].price.id
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

# Zugriff prüfen
def is_access_granted():
    return any([
        session.get("free_unlocked"),
        session.get("plus_unlocked"),
        session.get("pro_unlocked")
    ])

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
    return "✅ Du wurdest abgemeldet."

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

# Formularverarbeitung
@app.route("/submit_form", methods=["POST"])
def submit_form():
    if not is_access_granted():
        return "❌ Zugriff verweigert – bitte zuerst Zugang aktivieren", 403

    name = request.form.get("name", "Unbekannt")
    assets = request.form.get("assets", "")
    beneficiaries = request.form.get("beneficiaries", "")
    message = request.form.get("message", "")
    identity = request.form.get("identity", "")
    typ = request.form.get("typ", "Echo Vault")
    uploaded_files = request.files.getlist("file")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Echo Vault – Digitales Vermächtnis\n\nKategorie: {typ}\n\nName: {name}")
    pdf.multi_cell(0, 10, f"Hinterlassene Inhalte: {assets}")
    pdf.multi_cell(0, 10, f"Empfänger: {beneficiaries}")
    pdf.multi_cell(0, 10, f"Letzte Nachricht:\n{message}")
    pdf.multi_cell(0, 10, f"Persönlichkeitsbeschreibung:\n{identity}")

    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "EchoVault_Dokument.pdf")
    pdf.output(pdf_path)

    for file in uploaded_files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(temp_dir, filename))

    return send_file(pdf_path, as_attachment=True, download_name="EchoVault_Dokument.pdf")

# Server starten
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
