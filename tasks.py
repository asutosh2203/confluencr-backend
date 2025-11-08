import sys
import os
import datetime
import time
from celery import Celery
from models import Transaction, SessionLocal
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

REDIS_URL = os.environ.get('REDIS_URL')

celery = Celery(
    __name__,
    broker=REDIS_URL,
    backend=REDIS_URL
)

# connect celery to Flask


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        from app import app
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

# Define the Background Task


@celery.task
def process_transaction(transaction_id):

    db = SessionLocal()
    try:
        # The 30-second simulated work
        time.sleep(30)

        # Find the transaction in the DB
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()

        if transaction:
            # Update the status and processed_at time
            transaction.status = "PROCESSED"
            transaction.processed_at = datetime.datetime.now()

            db.commit()

            print(f"FINISHED PROCESSING FOR: {transaction_id}")
            return f"Processed {transaction_id}"
        else:
            print(f"ERROR: Transaction {transaction_id} not found in DB.")
            return f"Error: {transaction_id} not found"

    except Exception as e:
        db.rollback()  # Rollback on error
        print(f"ERROR processing {transaction_id}: {e}")
        return f"Error: {e}"
    finally:
        db.close()
