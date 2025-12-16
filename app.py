from flask import Flask, render_template, redirect, url_for
from models import Coffee, Order

app = Flask(__name__, static_folder='static')

menu = [
    Coffee("Espresso", 2.5),
    Coffee("Latte", 3.5),
    Coffee("Cappuccino", 3.0),
    Coffee("Mocha", 4.0)
]

order = Order()

@app.route("/")
def index():
    return render_template("menu.html", menu=menu, order=order)

@app.route("/add/<int:item_id>")
def add(item_id):
    order.add_item(menu[item_id])
    return redirect(url_for("index"))

@app.route("/checkout")
def checkout():
    total = order.total()
    order.clear()
    return render_template("checkout.html", total=total)  

if __name__ == "__main__":
    app.run(debug=True)