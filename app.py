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


# Home/Menu Page
@app.route("/")
def index():
    menu = Coffee.query.filter_by(in_stock=True).all()
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    return render_template("menu.html", menu=menu, cart_count=cart_count)


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
    
    # Check if item already in cart
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
        # Create order
        new_order = Order(
            user_id=current_user.id,
            total=total,
            delivery_address=form.delivery_address.data,
            payment_method=form.payment_method.data
        )
        db.session.add(new_order)
        db.session.flush()
        
        # Add order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                coffee_id=item.coffee_id,
                quantity=item.quantity,
                price=item.coffee.price
            )
            db.session.add(order_item)
        
        # Clear cart
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


# Initialize database on first request
@app.before_request
def init_db():
    if not hasattr(app, '_db_initialized'):
        db.create_all()
        
        # Add sample coffees if database is empty
        if Coffee.query.count() == 0:
            sample_coffees = [
                Coffee(name="Espresso", price=2.5, description="Strong and bold", category="Hot"),
                Coffee(name="Latte", price=3.5, description="Smooth and creamy", category="Hot"),
                Coffee(name="Cappuccino", price=3.0, description="Classic Italian coffee", category="Hot"),
                Coffee(name="Mocha", price=4.0, description="Chocolate lover's delight", category="Hot"),
                Coffee(name="Americano", price=2.8, description="Bold and simple", category="Hot"),
                Coffee(name="Macchiato", price=3.2, description="Espresso with a touch of milk", category="Hot"),
                Coffee(name="Cold Brew", price=4.5, description="Smooth cold coffee", category="Cold"),
                Coffee(name="Iced Latte", price=4.0, description="Refreshing iced latte", category="Cold")
            ]
            db.session.bulk_save_objects(sample_coffees)
            db.session.commit()
            print("Sample coffees added to database!")
        
        app._db_initialized = True


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)