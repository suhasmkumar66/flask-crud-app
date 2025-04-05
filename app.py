from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///notes.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create tables
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Note model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            print(f"Attempting to register user: {username}")  # Log registration attempt
            
            if not username or not password:
                flash('Username and password are required')
                return redirect(url_for('register'))
            
            # Check if user exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists')
                return redirect(url_for('register'))
            
            # Create new user
            user = User(username=username)
            user.set_password(password)
            
            # Add to database
            db.session.add(user)
            print("Attempting to commit user to database...")  # Log before commit
            db.session.commit()
            print("User successfully committed to database")  # Log after commit
            
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            error_msg = f"Registration error: {str(e)}"
            print(error_msg)  # Log the error
            flash(f'Registration failed: {str(e)}')  # Show the actual error to user
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
    return render_template('dashboard.html', notes=notes)

@app.route('/notes/create', methods=['GET', 'POST'])
@login_required
def create_note():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        note = Note(title=title, content=content, user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        
        flash('Note created successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('create_note.html')

@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash('You do not have permission to edit this note')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        db.session.commit()
        
        flash('Note updated successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_note.html', note=note)

@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash('You do not have permission to delete this note')
        return redirect(url_for('dashboard'))
    
    db.session.delete(note)
    db.session.commit()
    
    flash('Note deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/debug/db')
def debug_db():
    try:
        db.engine.connect()
        return "Database connection successful"
    except Exception as e:
        return f"Database connection failed: {str(e)}"

@app.route('/debug/tables')
def debug_tables():
    try:
        # Get all table names using inspect
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        return f"Database tables: {tables}"
    except Exception as e:
        return f"Error checking tables: {str(e)}"

@app.route('/debug/create-tables')
def create_tables():
    try:
        with app.app_context():
            db.create_all()
            return "Tables created successfully"
    except Exception as e:
        return f"Error creating tables: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
    # Only run in development
    if os.getenv('FLASK_ENV') != 'production':
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 80)))
