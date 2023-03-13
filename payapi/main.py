import json
import os
import stripe
from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, request
import requests
import backoff

load_dotenv()
stripe.api_key = os.environ.get("STRIPE_API_KEY")
stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
stripe.max_network_retries = int(os.environ.get("STRIPE_MAX_NET_RETRIES"))

app = Flask(__name__)
swagger = Swagger(app)


@app.route("/success")
def success():
    return "Success"


@app.route("/cancelled")
def cancelled():
    return "Cancelled"


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create Stripe Checkout session
    ---
    parameters:
          - in: body
            name: body
            schema:
              required:
                - user_id
                - name
              properties:
                user_name:
                  type: string
                  description: User name
                  example: Test user name
                user_id:
                  type: string
                  description: User ID
                  example: 124
                email:
                  type: string
                  description: User email
                  example: test@user.com
                product_name:
                  type: string
                  description: Product name
                  example: Test subscription
                currency:
                  type: string
                  description: Currency
                  example: USD
                amount:
                  type: integer
                  description: Product price
                  example: 10000
                order_id:
                  type: integer
                  description: Order ID
                  example: 12897

    responses:
      200:
        description: Checkout session created
    """
    payment_method_id = None
    request_data = request.get_json()
    user_id = request_data["user_id"]
    email = request_data["email"]
    customer_search = stripe.Customer.search(
        query=f'metadata["int_customer_id"]:"{user_id}"'
    )
    if customer_search.data:
        customer_id = customer_search.data[0]["id"]
        payment_methods = stripe.PaymentMethod.list(customer=customer_id)
        if payment_methods.data:
            payment_method_id = payment_methods.data[0]["id"]
    else:
        new_customer = stripe.Customer.create(
            name=request_data["user_name"],
            email=email,
            metadata={"int_customer_id": f"{user_id}"},
        )
        customer_id = new_customer["id"]
    if payment_method_id:
        try:
            stripe.PaymentIntent.create(
                description=request_data["product_name"],
                amount=request_data["amount"],
                currency=request_data["currency"],
                customer=customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
                metadata={"order_id": f"{request_data['order_id']}"},
            )
        except stripe.error.CardError as e:
            err = e.error
            # Error code will be authentication_required if authentication is needed
            print("Code is: %s" % err.code)
            payment_intent_id = err.payment_intent["id"]
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return jsonify(success=True, url=None)
    else:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": f"{request_data['currency']}",
                        "product_data": {
                            "name": f"{request_data['product_name']}",
                        },
                        "unit_amount": f"{request_data['amount']}",
                    },
                    "quantity": 1,
                }
            ],
            customer=customer_id,
            metadata={"order_id": "6735"},
            mode="payment",
            success_url="http://localhost:4242/success",
            cancel_url="http://localhost:4242/cancel",
            payment_intent_data={
                "setup_future_usage": "off_session",
                "metadata": {"order_id": f"{request_data['order_id']}"},
            },
        )
        return jsonify(success=True, url=session.url)


@app.route("/refund", methods=["POST"])
def refund():
    """Refund
    ---
    parameters:
          - in: body
            name: body
            schema:
              required:
                - payment_intent
              properties:
                payment_intent:
                  type: string
                  description: payment intent ID
    responses:
      200:
        description: Order refunded
    """
    request_data = request.get_json()
    payment_intent = request_data["payment_intent"]
    if payment_intent:
        stripe.Refund.create(payment_intent=payment_intent)
        return jsonify(success=True)


@app.route("/webhook", methods=["POST"])
def webhook():
    event = None
    payload = request.get_data(as_text=True)

    try:
        event = json.loads(payload)
    except ValueError as e:
        print("⚠️  Webhook error while parsing basic request." + str(e))
        return jsonify(success=False)
    if stripe_webhook_secret:
        sig_header = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_webhook_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print("⚠️  Webhook signature verification failed." + str(e))
            return jsonify(success=False)

    if event and event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        order_id = payment_intent["metadata"]["order_id"]
        send_successful_payment(order_id=order_id)
    return jsonify(success=True)


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
def send_successful_payment(self, order_id):
    dictToSend = {'order_id': f"{order_id}"}
    res = requests.post('http://localhost:5000/add-payment', json=dictToSend)

if __name__ == "__main__":
    app.run(port=4242)
