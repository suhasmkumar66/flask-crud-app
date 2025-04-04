from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=True)

# Initialize the database properly
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "Welcome to the Flask CRUD API!! Use /items to interact."

# Create (POST)
@app.route("/items", methods=["POST"])
def create_item():
    data = request.json
    new_item = Item(name=data["name"], description=data.get("description", ""))
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Item created successfully"}), 201

# Read (GET all)
@app.route("/items", methods=["GET"])
def get_items():
    items = Item.query.all()
    return jsonify([{"id": item.id, "name": item.name, "description": item.description} for item in items])

# Read (GET one)
@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({"id": item.id, "name": item.name, "description": item.description})

# Update (PUT)
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json
    item.name = data["name"]
    item.description = data.get("description", item.description)
    db.session.commit()
    return jsonify({"message": "Item updated successfully"})

# Delete (DELETE)
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted successfully"})

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
