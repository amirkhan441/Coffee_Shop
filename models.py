from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Coffee(db.Model):
    __tablename__ = 'coffees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<Coffee {self.name}>'


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')
    
    # Relationship with order items
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    coffee_id = db.Column(db.Integer, db.ForeignKey('coffees.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    
    # Relationship with coffee
    coffee = db.relationship('Coffee', backref='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'


class Cart:
    """Session-based cart for temporary storage before checkout"""
    def __init__(self):
        self.items = []
    
    def add_item(self, coffee):
        # Check if item already exists in cart
        for item in self.items:
            if item['coffee'].id == coffee.id:
                item['quantity'] += 1
                return
        # Add new item
        self.items.append({
            'coffee': coffee,
            'quantity': 1
        })
    
    def total(self):
        return sum(item['coffee'].price * item['quantity'] for item in self.items)
    
    def clear(self):
        self.items.clear()
    
    def get_items(self):
        return self.items