from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Coffee, Order, OrderItem, CartItem
from forms import RegistrationForm, LoginForm, CheckoutForm
from config import Config
import os

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# DATABASE INITIALIZATION ROUTE (Use this first!)
@app.route("/init-database-secret-xyz-123")
def init_database():
    try:
        with app.app_context():
            # Drop all old tables
            db.drop_all()
            print("✅ Old tables dropped")
            
            # Create new tables with all columns
            db.create_all()
            print("✅ New tables created")
            
            # Add sample coffees
            sample_coffees = [
                Coffee(name="Espresso", price=2.5, description="Strong and bold", category="Hot", in_stock=True),
                Coffee(name="Latte", price=3.5, description="Smooth and creamy", category="Hot", in_stock=True),
                Coffee(name="Cappuccino", price=3.0, description="Classic Italian", category="Hot", in_stock=True),
                Coffee(name="Mocha", price=4.0, description="Chocolate delight", category="Hot", in_stock=True),
                Coffee(name="Americano", price=2.8, description="Bold and simple", category="Hot", in_stock=True),
                Coffee(name="Macchiato", price=3.2, description="Espresso with milk", category="Hot", in_stock=True),
                Coffee(name="Cold Brew", price=4.5, description="Smooth cold coffee", category="Cold", in_stock=True),
                Coffee(name="Iced Latte", price=4.0, description="Refreshing iced latte", category="Cold", in_stock=True)
            ]
            db.session.bulk_save_objects(sample_coffees)
            db.session.commit()
            print("✅ Sample data added")
            
            total_coffees = Coffee.query.count()
            total_users = User.query.count()
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Database Initialized</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #2c1810 0%, #4a2c1a 100%);
                        color: #d4a574;
                        padding: 50px;
                        text-align: center;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .container {{
                        background: rgba(0, 0, 0, 0.6);
                        padding: 50px;
                        border-radius: 20px;
                        border: 3px solid #d4a574;
                        max-width: 600px;
                    }}
                    h1 {{ font-size: 2.5em; margin-bottom: 30px; }}
                    p {{ font-size: 1.2em; margin: 15px 0; }}
                    .stats {{ 
                        background: rgba(212, 165, 116, 0.1);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 30px 0;
                    }}
                    a {{
                        display: inline-block;
                        background: #d4a574;
                        color: #2c1810;
                        padding: 15px 40px;
                        text-decoration: none;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 1.2em;
                        margin-top: 20px;
                        transition: all 0.3s ease;
                    }}
                    a:hover {{
                        transform: scale(1.05);
                        box-shadow: 0 5px 15px rgba(212, 165, 116, 0.5);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Database Initialized!</h1>
                    <div class="stats">
                        <p><strong>Tables Created:</strong></p>
                        <p>users, coffees, cart_items, orders, order_items</p>
                        <p style="margin-top: 20px;"><strong>Total Coffees:</strong> {total_coffees}</p>
                        <p><strong>Total Users:</strong> {total_users}</p>
                    </div>
                    <a href="/">Go to Coffee Shop →</a>
                </div>
            </body>
            </html>
            """
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #2c1810;
                    color: #ff6b6b;
                    padding: 50px;
                }}
                .error-box {{
                    background: rgba(220, 53, 69, 0.1);
                    padding: 30px;
                    border-radius: 15px;
                    border: 2px solid #ff6b6b;
                }}
                pre {{
                    background: rgba(0, 0, 0, 0.5);
                    padding: 20px;
                    border-radius: 10px;
                    overflow-x: auto;
                    color: #e8d5c4;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>❌ Database Initialization Error</h1>
                <h3>Error Message:</h3>
                <p>{str(e)}</p>
                <h3>Full Traceback:</h3>
                <pre>{error_details}</pre>
                <a href="/" style="color: #d4a574; font-size: 1.2em; margin-top: 20px; display: inline-block;">Try Again</a>
            </div>
        </body>
        </html>
        """


# Home/Menu Page
@app.route("/")
def index():
    try:
        menu = Coffee.query.filter_by(in_stock=True).all()
        cart_count = 0
        if current_user.is_authenticated:
            cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
        return render_template("menu.html", menu=menu, cart_count=cart_count)
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; background: #2c1810; color: #ff6b6b; padding: 50px; text-align: center;">
            <h1>⚠️ Database Not Initialized</h1>
            <p style="font-size: 1.2em; color: #e8d5c4;">Please initialize the database first:</p>
            <a href="/init-database-secret-xyz-123" 
               style="display: inline-block; background: #d4a574; color: #2c1810; 
                      padding: 15px 40px; text-decoration: none; border-radius: 10px; 
                      font-weight: bold; font-size: 1.2em; margin-top: 30px;">
                Initialize Database
            </a>
            <p style="margin-top: 30px; color: #888; font-size: 0.9em;">Error: {str(e)}</p>
        </body>
        </html>
        """


# Registration
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


# Login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login failed. Please check email and password.', 'danger')
    
    return render_template('login.html', form=form)


# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# Add to Cart
@app.route("/add/<int:item_id>")
@login_required
def add(item_id):
    coffee = Coffee.query.get_or_404(item_id)
    
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        coffee_id=coffee.id
    ).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, coffee_id=coffee.id)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{coffee.name} added to cart!', 'success')
    return redirect(url_for("index"))


# View Cart
@app.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.subtotal() for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total)


# Update Cart Quantity
@app.route("/cart/update/<int:item_id>/<action>")
@login_required
def update_cart(item_id, action):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('cart'))
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart.', 'info')
            return redirect(url_for('cart'))
    
    db.session.commit()
    return redirect(url_for('cart'))


# Remove from Cart
@app.route("/cart/remove/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


# Checkout
@app.route("/checkout", methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('index'))
    
    form = CheckoutForm()
    total = sum(item.subtotal() for item in cart_items)
    
    if form.validate_on_submit():
        new_order = Order(
            user_id=current_user.id,
            total=total,
            delivery_address=form.delivery_address.data,
            payment_method=form.payment_method.data
        )
        db.session.add(new_order)
        db.session.flush()
        
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                coffee_id=item.coffee_id,
                quantity=item.quantity,
                price=item.coffee.price
            )
            db.session.add(order_item)
        
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        flash(f'Order placed successfully! Order ID: #{new_order.id}', 'success')
        return redirect(url_for('order_success', order_id=new_order.id))
    
    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)


# Order Success Page
@app.route("/order/success/<int:order_id>")
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    return render_template("order_success.html", order=order)


# Order History
@app.route("/orders")
@login_required
def view_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)