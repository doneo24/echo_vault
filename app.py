from flask import Flask, request, jsonify, send_file
import openai
import os
import tempfile
from fpdf import FPDF

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")  # <- setze das in Render als Env Variable

@app.route("/generate_will", methods=["POST"])
def generate_will():
    data = request.json
    name = data.get("name")
    age = data.get("age")
    assets = data.get("assets", [])
    beneficiaries = data.get("beneficiaries", {})

    # Texte zusammenbauen für den Prompt
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
        response = openai.ChatCompletion.create(
