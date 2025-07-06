# Import necessary modules from Flask
from flask import Flask, request, render_template_string, redirect, url_for, session, flash, g, render_template
import os # Needed for session secret key
import sqlite3 # For database operations
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing
from flask_mail import Mail, Message
from flask import Flask, render_template, jsonify
import json
import os
from flask import send_from_directory
import stripe
from flask import render_template_string

from dotenv import load_dotenv
import os

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
price_id = os.getenv("STRIPE_PRICE_ID")

# --- Configuration ---
# Create a Flask application instance
app = Flask(__name__)

# Secret key for session management. Keep this secret in a real application!
app.secret_key = os.urandom(24) # Generates a random secret key

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'penguinstokyo@gmail.com'  # ←自分のGmailアドレス
app.config['MAIL_PASSWORD'] = 'qesk lrww cwkj choo'     # これがGmailアプリパスワード
app.config['MAIL_DEFAULT_SENDER'] = 'penguinstokyo@gmail.com'

mail = Mail(app)
# Database configuration
DATABASE = 'users.db' # Name of the SQLite database file

# --- Database Helper Functions ---

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES # Detect data types
        )
        g.db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return g.db
    
@app.teardown_appcontext
def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with sqlite3.connect('users.db') as conn:
        db = conn.cursor()

        # users テーブル
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0
            )
        ''')

        # user_progress テーブル
        db.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quiz_id TEXT,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
# Initialize the database when the app starts

# --- HTML Template (No changes needed from previous version) ---
html_template = """
<!DOCTYPE html>
<html lang="en"> <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log in / Registration</title> <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                }
            }
        }
    </script>
    <style>
    /* Basic body styling */
    body {
        font-family: 'Noto Sans JP', 'Helvetica Neue', Arial, sans-serif;
        background: url('/static/images/allmate.png') no-repeat center center fixed;
        background-size: cover;
        color: #444; /* 柔らかい色 */
        margin: 0;
        padding: 0;
    }

    /* Style for the container */
    .form-container {
        background-color: rgba(255, 255, 245, 0.85);
        backdrop-filter: blur(8px);
        border-radius: 1.5rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        padding: 2.5rem;
        width: 90%;
        max-width: 480px;
        margin: 5vh auto;
        border: 2px solid #d6cfc7;
    }

    /* Style for input fields */
    .input-field {
        border-radius: 0.75rem;
        border: 1px solid #ccc;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        width: 100%;
        margin-bottom: 1.2rem;
        background-color: #fafafa;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }

    .input-field:focus {
        outline: none;
        border-color: #a3b18a; /* 柔らかい緑 */
        box-shadow: 0 0 5px rgba(163, 177, 138, 0.5);
        background-color: #ffffff;
    }

    /* Style for buttons */
    .submit-button {
        border-radius: 0.75rem;
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        color: white;
        background: linear-gradient(to right, #7ca982, #a3b18a);
        transition: background 0.3s ease, transform 0.2s ease;
        box-shadow: 0 5px 10px rgba(124, 169, 130, 0.4);
        cursor: pointer;
        border: none;
        width: 100%;
    }

    .submit-button:hover {
        background: linear-gradient(to right, #5e8369, #87a278);
        transform: translateY(-3px);
    }

    .submit-button:active {
        transform: translateY(0px);
    }

    /* Style for toggle links */
    .toggle-link {
        color: #6c8b5b;
        font-weight: 500;
        cursor: pointer;
        transition: color 0.3s ease;
        text-decoration: none;
        font-size: 0.95rem;
    }

    .toggle-link:hover {
        color: #4f6f48;
        text-decoration: underline;
    }

    /* Hide elements */
    .hidden {
        display: none;
    }

    /* Message styling */
    .message {
        margin-bottom: 1rem;
        text-align: center;
        font-size: 0.9rem;
        font-weight: 500;
        padding: 0.6rem;
        border-radius: 0.5rem;
    }

    .message-error {
        color: #b94a48;
        background-color: #f2dede;
        border: 1px solid #ebcccc;
    }

    .message-success {
        color: #468847;
        background-color: #dff0d8;
        border: 1px solid #d6e9c6;
    }
</style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

    <div class="form-container">

        <div id="login-form" class="{{ 'hidden' if register_form_active else '' }}">
            <h2 class="text-3xl font-bold text-center text-gray-800 mb-6">Welcome Back!</h2> {% with messages = get_flashed_messages(category_filter=["login_error", "login_success"]) %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="message {{ 'message-error' if 'error' in get_flashed_messages(with_categories=true)[0][0] else 'message-success' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form action="/login" method="post">
                <div class="mb-4">
                    <label for="login-username" class="block text-sm font-medium text-gray-700 mb-1">Username</label> <input type="text" id="login-username" name="username" required
                           class="w-full input-field" placeholder="Enter your username"> </div>
                <div class="mb-6">
                    <label for="login-password" class="block text-sm font-medium text-gray-700 mb-1">Password</label> <input type="password" id="login-password" name="password" required
                           class="w-full input-field" placeholder="Enter your password"> </div>
                <button type="submit" class="w-full submit-button mb-4">Log in</button> </form>
            <p class="text-center text-sm text-gray-600">
                Don't have an account yet? <span onclick="toggleForms()" class="toggle-link">Register here</span> </p>
        </div>

        <div id="register-form" class="{{ '' if register_form_active else 'hidden' }}">
            <h2 class="text-3xl font-bold text-center text-gray-800 mb-6">Create your account</h2> {% with messages = get_flashed_messages(category_filter=["register_error", "register_success"]) %}
                {% if messages %}
                    {% for message in messages %}
                         <div class="message {{ 'message-error' if 'error' in get_flashed_messages(with_categories=true)[0][0] else 'message-success' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form action="/register" method="post">
                <div class="mb-4">
                    <label for="register-username" class="block text-sm font-medium text-gray-700 mb-1">Username</label> <input type="text" id="register-username" name="username" required
                           class="w-full input-field" placeholder="Create a username"> </div>
                 <div class="mb-4">
                    <label for="register-email" class="block text-sm font-medium text-gray-700 mb-1">Email Address</label> <input type="email" id="register-email" name="email" required
                           class="w-full input-field" placeholder="Enter your Email Address"> </div>
                <div class="mb-6">
                    <label for="register-password" class="block text-sm font-medium text-gray-700 mb-1">Password</label> <input type="password" id="register-password" name="password" required
                           class="w-full input-field" placeholder="Create a pasword"> </div>
                <button type="submit" class="w-full submit-button mb-4">Registration</button> </form>
            <p class="text-center text-sm text-gray-600">
                Already have an account? <span onclick="toggleForms()" class="toggle-link">Login here</span> </p>
        </div>

    </div>

    <script>
        // Function to toggle between login and registration forms
        function toggleForms() {
            const loginForm = document.getElementById('login-form');
            const registerForm = document.getElementById('register-form');
            const wasLoginHidden = loginForm.classList.contains('hidden');
            loginForm.classList.toggle('hidden', !wasLoginHidden);
            registerForm.classList.toggle('hidden', wasLoginHidden);
            const messages = document.querySelectorAll('.message');
            messages.forEach(msg => msg.style.display = 'none');
            const url = new URL(window.location);
            if (registerForm.classList.contains('hidden')) {
                url.searchParams.delete('show_register');
            } else {
                url.searchParams.set('show_register', 'true');
            }
        }
        // Determine initial form visibility
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const showRegisterParam = urlParams.get('show_register');
            const hasRegisterError = document.querySelector('#register-form .message-error') !== null;
            if (showRegisterParam === 'true' || hasRegisterError) {
                 document.getElementById('register-form').classList.remove('hidden');
                 document.getElementById('login-form').classList.add('hidden');
            } else {
                 document.getElementById('login-form').classList.remove('hidden');
                 document.getElementById('register-form').classList.add('hidden');
            }
        });
    </script>

</body>
</html>
"""

# --- Routes ---

@app.route('/')
def index():
    """Serves the main login/registration page."""
    if 'user_id' in session: # Check for user_id in session now
        return redirect(url_for('welcome'))
    show_register = request.args.get('show_register', 'false').lower() == 'true'
    return render_template_string(html_template, register_form_active=show_register)


@app.route('/login', methods=['POST'])
def login():
    """Handles the login form submission using database."""
    username = request.form.get('username')
    password = request.form.get('password')
    error = None
    db = get_db()
    user = None # Initialize user variable

    if not username or not password:
        error = "Please enter your username and password" # Japanese
        flash(error, "login_error")
        return redirect(url_for('index'))

    try:
        # Fetch user from database by username
        cursor = db.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error during login: {e}")
        error = "An error has occurred during login" # Japanese
        flash(error, "login_error")
        return redirect(url_for('index'))

    if user is None:
        error = 'The username does not exist' # Japanese
    elif not check_password_hash(user['password_hash'], password):
        # Check the hashed password
        error = 'The password is required' # Japanese

    if error is None:
        # Login successful - store user ID in session
        session.clear() # Clear old session data
        session['user_id'] = user['id'] # Store user ID instead of username
        session['username'] = user['username'] # Keep username for display if needed
        # Redirect to the personalized welcome page
        return redirect(url_for('home'))
    else:
        # Login failed
        flash(error, "login_error")
        return redirect(url_for('index'))


@app.route('/register', methods=['POST'])
def register():
    """Handles the registration form submission using database."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    db = get_db()
    error = None

    if not username:
        error = 'Username is required' # Japanese
    elif not email:
        error = 'Email address is required' # Japanese
    elif not password:
        error = 'Password is required' # Japanese

    if error:
        flash(error, "register_error")
        # Redirect back, ensuring register form is shown
        return redirect(url_for('index', show_register='true'))

    try:
        # Hash the password securely
        hashed_password = generate_password_hash(password)
        # Insert the new user into the database
        db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, hashed_password)
        )
        db.commit() # Commit the changes to the database
        print(f"Registered new user: {username}") # Log registration
    except sqlite3.IntegrityError:
        # This error occurs if the username is already taken (due to UNIQUE constraint)
        error = f"The username '{username}' is already taken" # Japanese
        flash(error, "register_error")
        return redirect(url_for('index', show_register='true'))
    except sqlite3.Error as e:
        # Handle other potential database errors during insertion
        print(f"Database error during registration: {e}")
        error = "An error has occurred registration" # Japanese
        flash(error, "register_error")
        return redirect(url_for('index', show_register='true'))
    else:
        # Registration successful
        flash("Registration has completed successfully. Please log in", "login_success") # Japanese
        # Redirect to the index page, showing the login form
        return redirect(url_for('index', show_register='false'))


@app.route('/welcome')
def welcome():
    """A simple page shown after successful login. Can be personalized later."""
    if 'user_id' not in session:
        # If user is not logged in, redirect to login page
        return redirect(url_for('index'))

    # Get username from session for display
    # You could fetch more user details from the DB using session['user_id'] here
    username = session.get('username', 'Guest') # Default to Guest if somehow username isn't set

    # --- Personalization Example (Requires DB changes and data) ---
    # db = get_db()
    # user_data = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    # last_lesson = user_data['last_lesson'] if user_data else '未設定'
    # quiz_score = user_data['quiz_score'] if user_data else 0
    # ----------------------------------------------------------------

    # Simple welcome message page
    return render_template("home.html")

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.clear() # Clear all session data (user_id, username)
    flash("Logged out。", "login_success") # Japanese
    return redirect(url_for('index')) # Redirect to login page

@app.route('/Osaka')
def Osaka():
    return render_template('Osaka/osaka-dialect.html')
@app.route('/dailyconv')
def dailyconv():
    return render_template('DailyConv/daily.html')
@app.route('/dailyconv/daily-<int:num>.html')
def dailyconv_page(num):
    return render_template(f'DailyConv/daily-{num}.html')
@app.route('/dailyconv/daily.html')
def dailyconv_main():
    return render_template('DailyConv/daily.html')
@app.route('/jlptlower')
def jlptlower():
    return render_template('JLPTLOWER/jlptlower.html')
@app.route('/jlptupper')
def jlptupper():
    return render_template('JLPTUPPER/jlptupper.html')

@app.route('/quiz-gate')
def quiz_gate():
    return render_template('quiz_gate.html')
@app.route('/premium')
def premium():
    return render_template('Premium/paid.html')
@app.route('/slangs')
def slang_home():
    return render_template('Slangs/slangs.html')
@app.route('/donation', endpoint='donation_home')
def donation():
    return render_template('donation.html')

@app.route('/slangs/<name>')
def slang_page(name):
    name = name.replace(".html", "")
    return render_template(f'Slangs/{name}.html')
@app.route('/reset_progress/<level>', methods=['POST'])
def reset_progress(level):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    db = get_db()
    user_id = session['user_id']
    # 該当levelのprogressだけリセット
    db.execute("DELETE FROM user_progress WHERE user_id = ? AND quiz_id LIKE ?", (user_id, f"{level}-%"))
    db.commit()
    return '', 204

@app.route('/unlock')
def unlock_features():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    db = get_db()
    db.execute("UPDATE users SET is_premium = 1 WHERE id = ?", (session['user_id'],))
    db.commit()

    session['is_premium'] = True
    flash("You are now a Premium Member! 🔓", "success")
    return redirect(url_for('home'))

@app.route('/user_progress_status/<level>')
def user_progress_status(level):
    if 'user_id' not in session:
        return {'error': 'Unauthorized'}, 401

    db = get_db()
    user_id = session['user_id']

    # 1〜15までで正解している数を取得
    completed = db.execute(
        "SELECT COUNT(*) as cnt FROM user_progress WHERE user_id = ? AND quiz_id LIKE ? AND completed = 1 AND (CAST(SUBSTR(quiz_id, INSTR(quiz_id, '-') + 1) AS INTEGER) BETWEEN 1 AND 15)",
        (user_id, f"{level}-%")
    ).fetchone()

    user = db.execute("SELECT is_premium FROM users WHERE id = ?", (user_id,)).fetchone()

    return {
        'completed_count': completed['cnt'],
        'is_premium': user['is_premium']
    }
@app.route('/jsonquiz/<level>-<int:num>')
def json_quiz(level, num):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    db = get_db()
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    is_premium = user['is_premium']

    if num > 15 and not is_premium:
        flash("This quiz is for Premium Members.", "error")
        return redirect(url_for('premium'))

    json_path = f'static/data/{level}-{num}.json'
    try:
        with open(json_path, encoding='utf-8') as f:
            quiz_data = json.load(f)
    except FileNotFoundError:
        return "Quiz not found", 404

    template_name = "quiz_choice.html" if quiz_data.get("type") == "choice" else "quiz_reorder.html"

    background_image = f"/static/images/{level}.png"
    
    return render_template(
        template_name, 
        level=level, num=num, **quiz_data)

@app.route('/<level>-<int:num>')
def jlpt_quiz(level, num):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    db = get_db()
    user_id = session['user_id']
    quiz_id = f"{level}-{num}"
    json_path = os.path.join('static', 'data', f"{quiz_id}.json")

    if not os.path.exists(json_path):
        return render_template("quiz_type3.html", quiz_id=quiz_id)  # ファイルがなければ type3 相当のページへ

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    quiz_type = data.get("type", "").strip().lower()

    # クイズタイプごとに処理を分岐
    if quiz_type == "type1":
        return render_template("quiz_type1.html", quiz_data=data, questions=data.get("questions", []),quiz_id=quiz_id, quizLevel=level, quizNum=num)
    elif quiz_type == "type2":
        return render_template("quiz_type2.html", quiz_data=data, quiz_id=quiz_id,  questions=data.get("questions", []),quizLevel=level, quizNum=num)
    elif quiz_type == "type3":
        return render_template("quiz_type3.html", quiz_data=data, quiz_id=quiz_id, quizLevel=level, quizNum=num)
    else:
        return render_template("quiz_type3.html", quiz_data=data, quiz_id=quiz_id, quizLevel=level, quizNum=num)  # 未定義typeもtype3扱い


@app.route('/<level>')
def jlpt_index(level):
    if not level.startswith("jlpt"):
        return "Not Found", 404  # JLPT以外のURLをブロック

    if 'user_id' not in session:
        return redirect(url_for('index'))

    db = get_db()
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    is_premium = user['is_premium']

    quizzes = db.execute(
        "SELECT quiz_id FROM user_progress WHERE user_id = ? AND quiz_id LIKE ?", 
        (user_id, f"{level}-%")
    ).fetchall()
    completed_quizzes = [q['quiz_id'] for q in quizzes]

    max_unlocked = 15

    if is_premium:
        while all(f"{level}-{i}" in completed_quizzes for i in range(max_unlocked - 4, max_unlocked + 1)):
            max_unlocked += 5

    return render_template(
        f"{level.upper()}FREE/{level}.html",
        is_premium=is_premium,
        completed_quizzes=completed_quizzes,
        max_unlocked=max_unlocked
    )


@app.route('/complete_quiz/<quiz_id>', methods=['POST'])
def complete_quiz(quiz_id):
    if 'user_id' not in session:
        return "Unauthorized", 401

    db = get_db()
    user_id = session['user_id']

    existing = db.execute(
        "SELECT * FROM user_progress WHERE user_id = ? AND quiz_id = ?",
        (user_id, quiz_id)
    ).fetchone()

    if existing:
        db.execute(
            "UPDATE user_progress SET completed = 1 WHERE user_id = ? AND quiz_id = ?",
            (user_id, quiz_id)
        )
    else:
        db.execute(
            "INSERT INTO user_progress (user_id, quiz_id, completed) VALUES (?, ?, 1)",
            (user_id, quiz_id)
        )
    db.commit()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return {"is_premium": user['is_premium']}

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='images/favicon.ico'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # ログインしてないと戻す
    return render_template('home.html')
@app.route('/<level>-<int:num>.json')
def serve_json_file(level, num):
    filepath = os.path.join('static', 'data', f'{level}-{num}.json')
    if os.path.exists(filepath):
        return app.send_static_file(f'data/{level}-{num}.json')
    else:
        return "JSON file not found", 404
    
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('first-name')
    lastname = request.form.get('last-name')
    email = request.form.get('email')
    message = request.form.get('message')

    full_message = f"From: {name} {lastname}\nEmail: {email}\n\nMessage:\n{message}"

    msg = Message("TokyoPenguins Contact Form",
                  recipients=["penguinstokyo@gmail.com"],  # ←メール受け取りたい自分のアドレス
                  body=full_message)

    try:
        mail.send(msg)
        flash("Message has sent🌸", "success")
    except Exception as e:
        print(e)
        flash("Failed to send a message. Please try again", "error")

    return redirect(url_for('home'))
# --- Run the Application ---

    # Runs the Flask development server
    # Debug=True enables auto-reloading and detailed errors.
    # **IMPORTANT:** Set debug=False in production!
    # host='0.0.0.0' makes the server accessible on your network


@app.route('/static/data/<path:filename>')
def serve_quiz_json(filename):
    filepath = os.path.join('static', 'data', filename)
    if os.path.exists(filepath):
        return send_from_directory('static/data', filename)
    else:
        return "JSON file not found", 404
    
#これ全部donation関係のやつ
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    amount = int(request.form.get("amount", 3000))  # デフォルト3000円（$30）

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': amount,  # セント単位 (3000 = $30)
                    'product_data': {
                        'name': 'Nihongo Connect Donation',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:5001/donation-success',
            cancel_url='http://localhost:5001/donation-cancel',
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e), 400
@app.route('/donation-success')
def donation_success():
    return "<h1>Thank you for your support! 🌸</h1>"

@app.route('/donation-cancel')
def donation_cancel():
    return "<h1>❌ Donation was cancelled.You can try again anytime.</h1>"
@app.route('/charge', methods=['POST'])
def charge():
    data = request.get_json()
    try:
        stripe.Charge.create(
            amount=data['amount'],
            currency='usd',
            source=data['token'],
            description='Donation to Nihongo Connect'
        )
        return {'status': 'success'}, 200
    except stripe.error.StripeError as e:
        return {'error': str(e)}, 400
    
    #when ppl access to jason withough sny questions, return coming_soon.htmlで返す
@app.route('/donation-email', methods=['POST'])
def donation_email():
    email = request.form.get('email')
    
    if not email:
        flash("Please enter a valid email.", "error")
        return redirect(url_for('donation_home'))

    # 保存先がまだない場合：CSVなどに書くのも可
    with open('donor_emails.txt', 'a') as f:
        f.write(email + '\n')

    flash("Thank you! You’ll receive exclusive updates soon. ✨", "success")
    return redirect(url_for('donation_home'))






if __name__ == "__main__":
    init_db()
    print("Database initialized.")
    app.run(host="0.0.0.0", port=5001, debug=True)
    