import json
import stripe
from flasgger import Swagger
from flask import Flask, jsonify, request
import requests
import backoff
import logging

from core.config import settings

stripe.api_key = settings.stripe_api_key
stripe_webhook_secret = settings.stripe_webhook_secret
stripe.max_network_retries = int(settings.stripe_max_net_retries)

app = Flask(settings.project_name)
swagger = Swagger(app)


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
def send_successful_payment(order_id, user_id, payment_intent_id, amount):
    dict_to_send = {
        "order_id": f"{order_id}",
        "user_id": f"{user_id}",
        "payment_intent_id": f"{payment_intent_id}",
        "amount": amount,
    }
    res = requests.post(url=f"{settings.billing_url}/api/v1/billing/add-payment", json=dict_to_send)
    logging.debug("%s", res)


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
    logging.info(request_data)
    user_id = request_data["user_id"]
    email = request_data["email"]
    customer_search = stripe.Customer.search(query=f'metadata["int_customer_id"]:"{user_id}"')
    if customer_search.data:
        customer_id = customer_search.data[0]["id"]
        logging.info(f"create-checkout-session, Customer found - {customer_id}")
        payment_methods = stripe.PaymentMethod.list(customer=customer_id)
        if payment_methods.data:
            payment_method_id = payment_methods.data[0]["id"]
            logging.info(f"create-checkout-session, Using saved payment method - {payment_method_id}")
    else:
        new_customer = stripe.Customer.create(
            name=request_data["user_name"],
            email=email,
            metadata={"int_customer_id": f"{user_id}"},
        )
        customer_id = new_customer["id"]
        logging.info(f"create-checkout-session, New customer created - {customer_id}")
    if payment_method_id:
        try:
            payment_intent = stripe.PaymentIntent.create(
                description=request_data["product_name"],
                amount=request_data["amount"],
                currency=request_data["currency"],
                customer=customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
                metadata={"order_id": f"{request_data['order_id']}", "user_id": user_id},
            )
        except stripe.error.CardError as e:  # Error code will be authentication_required if authentication is needed
            err = e.error
            logging.error(f"CardError, {err.code}, payment_intent {payment_intent['id']}")
        logging.info(f"create-checkout-session, Payment Intent created - {payment_intent['id']}")
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
                        "unit_amount": f"{int(request_data['amount'])*100}",
                    },
                    "quantity": 1,
                }
            ],
            customer=customer_id,
            metadata={"order_id": f"{request_data['order_id']}"},
            mode="payment",
            success_url=settings.success_url,
            cancel_url=settings.cancel_url,
            payment_intent_data={
                "setup_future_usage": "off_session",
                "metadata": {"order_id": f"{request_data['order_id']}", "user_id": user_id},
            },
        )
        logging.info(f"create-checkout-session, Checkout Session created - {session['id']}")
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
                - payment_intent_id
              properties:
                payment_intent_id:
                  type: string
                  description: payment intent ID
    responses:
      200:
        description: Order refunded
    """
    request_data = request.get_json()
    payment_intent = request_data["payment_intent_id"]
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
        logging.error(f"⚠️  Webhook error while parsing basic request. {e}")
        return jsonify(success=False)
    if stripe_webhook_secret:
        sig_header = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, stripe_webhook_secret)
        except stripe.error.SignatureVerificationError as e:
            logging.error(f"⚠️  Webhook signature verification failed. {e}")
            return jsonify(success=False)

    if event and event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        order_id = payment_intent["metadata"]["order_id"]
        user_id = payment_intent["metadata"]["user_id"]
        logging.info(f"create-checkout-session, payment_intent.succeeded,order_id - {order_id}, user_id - {user_id}")
        send_successful_payment(
            order_id=order_id, user_id=user_id, payment_intent_id=payment_intent["id"], amount=100000
        )
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(port=4242)
