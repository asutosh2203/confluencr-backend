import datetime
from flask import Flask, jsonify, request
from tasks import process_transaction
from models import SessionLocal, Transaction, create_tables
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# create Transactions table
create_tables()

# Health check endpoint


@app.route("/")
def health_check():
    return jsonify(status="HEALTHY", current_time=datetime.datetime.now().isoformat())


# Webhook Receiver Endpoint
# POST /v1/webhooks/transactions
@app.route("/v1/webhooks/transactions", methods=["POST"])
def webhook_receiver():

    data = request.json
    transaction_id = data.get("transaction_id")

    if not transaction_id:
        return jsonify(error="Transaction ID is required."), 400

    db = SessionLocal()

    try:
        transaction = Transaction(transaction_id=transaction_id,
                                  source_account=data.get('source_account'),
                                  destination_account=data.get(
                                      'destination_account'),
                                  amount=data.get('amount'),
                                  currency=data.get('currency'),
                                  status="PROCESSING")

        db.add(transaction)
        db.commit()

        # Delay the process transaction
        process_transaction.delay(transaction_id)

    except IntegrityError:
        db.rollback()
        print(f"GOT DUPLICATE WEBHOOK: {transaction_id}")

    except Exception as e:
        db.rollback()
        print(f"Server Error: {e}")
        return jsonify(error="Sorry, something went wrong, please try again later"), 500

    finally:
        db.close()

    return "", 202

# Transaction Status Endpoint
# GET /v1/transactions/<transaction_id>


@app.route("/v1/transactions/<string:transaction_id>")
def get_transaction_status(transaction_id):

    db = SessionLocal()
    try:
        # Find the transaction in the DB
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()

        if not transaction:
            return jsonify(error="Sorry, we could not find the transaction"), 404

        return jsonify(
            transaction_id=transaction.transaction_id,
            source_account=transaction.source_account,
            destination_account=transaction.destination_account,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            created_at=transaction.created_at.isoformat(),
            processed_at=transaction.processed_at.isoformat(
            ) if transaction.processed_at else None
        )

    except Exception as e:
        print(f"Error in get_transaction_status: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        db.close()


# This is like app.listen(port)
if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Using port 5001 to avoid clashes
