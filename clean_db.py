from app import app, db
from models import URL, Product, PriceHistory

with app.app_context():
    print("Cleaning database...")
    URL.query.delete()
    Product.query.delete()
    PriceHistory.query.delete()
    db.session.commit()
    print("Database cleaned")
