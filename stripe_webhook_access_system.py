
import json
import os
from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# Stripe-Konfiguration
stripe.api_key = 'sk_live_your_secret_key_here'  # Ersetze durch deinen echten Secret Key
endpoint_secret = 'whsec_your_webhook_secret_here'  # Ersetze durch deinen Webhook-Secret

# Dateipfad zur Nutzer-Datenbank
USERS_FILE = 'paid_users.json'

# Stelle sicher, dass die Datei existiert
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return 'Ungültige Payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Ungültige Signatur', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('customer_email')
        price_id = session['metadata'].get('price_id') if session.get('metadata') else None

        user_data = {
            'email': email,
            'price_id': price_id,
            'plan': classify_plan(price_id),
        }

        # Speichere den Nutzer
        save_paid_user(user_data)

        print(f"Zahlung empfangen: {email} → {user_data['plan']}")

    return '', 200

def classify_plan(price_id):
    if price_id == 'price_1RPylqQjaqheqwMhHEWyGqDP':
        return 'pro'
    elif price_id == 'price_1RPymFQjaqheqwMhhN76SYLw':
        return 'plus'
    elif price_id == 'price_1RPyw7QjaqheqwMhA6Mfg6OH':
        return 'free'
    else:
        return 'unbekannt'

def save_paid_user(data):
    with open(USERS_FILE, 'r+') as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            users = []

        if not any(u['email'] == data['email'] for u in users):
            users.append(data)
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()

@app.route('/verify-access', methods=['POST'])
def verify_access():
    data = request.get_json()
    email = data.get('email')

    with open(USERS_FILE, 'r') as f:
        users = json.load(f)

    for user in users:
        if user['email'] == email:
            return jsonify({'access': True, 'plan': user['plan']})

    return jsonify({'access': False}), 403

if __name__ == '__main__':
    app.run(port=4242)
