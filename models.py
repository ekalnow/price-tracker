from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    platform = db.Column(db.String(50))  # 'salla', 'zid', etc.
    is_valid = db.Column(db.Boolean, default=True)
    last_checked = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    
    user = db.relationship('User', backref=db.backref('urls', lazy=True))
    product = db.relationship('Product', backref=db.backref('urls', lazy=True))
    
    def __repr__(self):
        return f'<URL {self.url}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    current_price = db.Column(db.Float)
    currency = db.Column(db.String(10), default='SAR')
    image_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    availability = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    price_history = db.relationship('PriceHistory', backref=db.backref('product', lazy=True), 
                                   order_by="desc(PriceHistory.timestamp)")
    
    @property
    def last_price_change(self):
        """Return the last price change percentage"""
        if len(self.price_history) >= 2:
            current = self.price_history[0].price
            previous = self.price_history[1].price
            if previous > 0:
                return ((current - previous) / previous) * 100
        return 0
    
    def __repr__(self):
        return f'<Product {self.name}>'

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceHistory {self.product_id}: {self.price} at {self.timestamp}>'

class PriceAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    alert_type = db.Column(db.String(20))  # 'below', 'above', 'percentage_change'
    percentage_threshold = db.Column(db.Float)  # For percentage change alerts
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('alerts', lazy=True))
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))
    
    def __repr__(self):
        return f'<PriceAlert {self.product_id} {self.alert_type} {self.target_price}>'
