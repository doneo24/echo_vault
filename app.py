from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import os
import tempfile
from fpdf import FPDF

app = Flask(__name__)

# Initialisiere OpenAI-Client mit neuem SDK
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

        "# PDF erstellen  pdf"
