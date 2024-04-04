from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from collaborative_filtering import CollaborativeFilteringRecommender  # Import the CollaborativeFilteringRecommender class

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/virtual_library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to your actual secret key

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer)
    educational_level = db.Column(db.String(50))

    liked_resources = db.relationship('LearningResource', secondary='user_likes', backref='liked_by')

class LearningResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content_type = db.Column(db.String(50))
    author = db.Column(db.String(100))
    rating = db.Column(db.Float)
    tags = db.Column(db.String(100))
    category = db.Column(db.String(100))
    url = db.Column(db.String(200))

user_likes = db.Table('user_likes',
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                      db.Column('learning_resource_id', db.Integer, db.ForeignKey('learning_resource.id'))
                      )

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

# Initialize and train the recommender
recommender = CollaborativeFilteringRecommender({})  # Initialize with empty user-item ratings

@app.route('/')
def login_redirect():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        age = request.form['age']
        educational_level = request.form['educational_level']

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password, age=age, educational_level=educational_level)
        db.session.add(new_user)
        db.session.commit()

        flash('You have been successfully registered!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search_query')

    results = LearningResource.query.filter(
        or_(
            LearningResource.title.contains(search_query),
            LearningResource.author.contains(search_query),
            LearningResource.tags.contains(search_query)
        )
    ).all()

    rating_similar_books = LearningResource.query.filter(
        LearningResource.rating.in_([book.rating for book in results])
    ).filter(
        LearningResource.id.notin_([book.id for book in results])
    ).all()

    shared_author_books = LearningResource.query.filter(
        LearningResource.author.in_([book.author for book in results])
    ).filter(
        LearningResource.id.notin_([book.id for book in results])
    ).all()

    # Generate recommendations for the current user
    user_id = current_user.id if current_user.is_authenticated else None
    if user_id:
        recommendations = recommender.get_recommendations(user_id)
    else:
        recommendations = []

    return render_template('search_results.html', results=results, rating_similar_books=rating_similar_books, shared_author_books=shared_author_books, recommendations=recommendations)

@app.route('/like_resource', methods=['GET', 'POST'])
@login_required
def like_resource():
    if request.method == 'POST':
        resource_id = request.form.get('resource_id')
        resource = LearningResource.query.get(resource_id)
        current_user.liked_resources.append(resource)
        db.session.commit()
        flash('Resource liked successfully!', 'success')
        return redirect(url_for('search'))
    else:
        flash('Method not allowed!', 'error')
        return redirect(url_for('search'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', current_user=current_user)

@app.route('/recommendations')
@login_required
def recommendations():
    liked_books = current_user.liked_resources
    return render_template('recommendations.html', liked_books=liked_books)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
