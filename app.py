from flask import Flask, render_template, redirect, url_for, session
from models import db, Coffee, Order, OrderItem, Cart
from config import Config, ProductionConfig, DevelopmentConfig
import os

app = Flask(__name__, static_folder='static')

# Environment-based config
if os.getenv('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Initialize database
db.init_app(app)

# Create a global cart object
cart = Cart()

# Database initialization - PRODUCTION MEIN BHI RUN HOGA
with app.app_context():
    db.create_all()
    # Add sample coffees if database is empty
    if Coffee.query.count() == 0:
        sample_coffees = [
            Coffee(name="Espresso", price=2.5),
            Coffee(name="Latte", price=3.5),
            Coffee(name="Cappuccino", price=3.0),
            Coffee(name="Mocha", price=4.0),
            Coffee(name="Americano", price=2.8),
            Coffee(name="Macchiato", price=3.2)
        ]
        db.session.bulk_save_objects(sample_coffees)
        db.session.commit()
        print("Sample coffees added to database!")

@app.route("/")
def index():
    menu = Coffee.query.all()
    return render_template("menu.html", menu=menu, order=cart)

@app.route("/add/<int:item_id>")
def add(item_id):
    coffee = Coffee.query.get_or_404(item_id)
    cart.add_item(coffee)
    return redirect(url_for("index"))

@app.route("/checkout")
def checkout():
    if not cart.items:
        return redirect(url_for("index"))
    
    total = cart.total()
    new_order = Order(total=total)
    db.session.add(new_order)
    db.session.flush()
    
    for item in cart.get_items():
        order_item = OrderItem(
            order_id=new_order.id,
            coffee_id=item['coffee'].id,
            quantity=item['quantity'],
            price=item['coffee'].price
        )
        db.session.add(order_item)
    
    db.session.commit()
    order_total = total
    cart.clear()
    
    return render_template("checkout.html", total=order_total)

@app.route("/orders")
def view_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)