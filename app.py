from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
from bson import ObjectId
import os
import requests

app = Flask(__name__, template_folder="templates")
app.secret_key = 'your_secret_key'
CORS(app)  # Allow cross-origin requests





# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["student_analyzer"]
users_collection = db["users"]
marks_collection = db["marks"]

# Mock data for demonstration
user_marks = {
    "user1": [85, 90, 78, 88, 76],
    "user2": [70, 80, 65, 75, 85]
}

# Serve index.html
@app.route("/")
def index():
    return render_template("index.html")

# Remove the /login-page route
# @app.route("/login-page")
# def login_page():
#     return render_template("login-page.html")

# Serve signup.html
@app.route("/signup-page")
def signup_page():
    return render_template("signup.html")

# Signup Route
@app.route("/signup", methods=["POST"])
def signup():
    data = request.form
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        flash("Username, email, and password are required.")
        return redirect(url_for("signup_page"))

    if users_collection.find_one({"$or": [{"email": email}, {"username": username}]}):
        flash("User already exists.")
        return redirect(url_for("signup_page"))

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users_collection.insert_one({"username": username, "email": email, "password": hashed_password})
    flash("Account created successfully. Please log in.")
    return redirect(url_for("login"))  # Redirect to the login route

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        # Safely retrieve form data
        name_or_email = request.form.get('nameOrEmail', '').strip()
        password = request.form.get('password', '').strip()
        
        if not name_or_email or not password:
            flash('Both Name/Email and Password are required.', 'error')
            return render_template("login.html")
        
        # Check if the input is an email or a name
        if '@' in name_or_email:
            user = find_user_by_email(name_or_email)
        else:
            user = find_user_by_name(name_or_email)
        
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            session['username'] = user["username"]
            return redirect(url_for("main_page"))
        else:
            flash('Invalid Name/Email or Password. Please try again.', 'error')
            return render_template("login.html")
    
    return render_template("login.html")

# Helper functions to find users
def find_user_by_email(email):
    return users_collection.find_one({"email": email})

def find_user_by_name(name):
    return users_collection.find_one({"username": name})

# Middleware to check if user is logged in
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash('You must be logged in to access this page.')
            return redirect(url_for("login_page"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Serve mainpg.html
@app.route("/main-page")
@login_required
def main_page():
    # Ensure the main page renders correctly
    return render_template("mainpg.html")

# Serve performance-entry-page.html
@app.route("/performance-entry-page")
@login_required
def performance_entry_page():
    return render_template("performance-entry-page.html")

# Handle marks submission (add new marks)
@app.route("/submit-marks", methods=["POST"])
@login_required
def submit_marks():
    username = session['username']
    try:
        marks = {
            "math": int(request.form.get("math", 0)),
            "science": int(request.form.get("science", 0)),
            "social": int(request.form.get("social", 0)),
            "computer": int(request.form.get("computer", 0)),
            "gk": int(request.form.get("gk", 0)),
        }
        # Add new marks to the database
        marks_collection.insert_one({"username": username, "marks": marks})
        
        # Recalculate recommendations based on the most recent marks
        latest_marks = marks  # Use the current marks submitted by the user

        recommendations = []

        for subject, mark in latest_marks.items():
            allow_topic_input = mark < 70  # Allow topic input for marks less than 70
            if mark < 35:
                recommendations.append({
                    "subject": subject.capitalize(),
                    "message": f"Your marks in {subject.capitalize()} are below 35. Focus on improving this subject.",
                    "resources": [
                        f"https://www.khanacademy.org/{subject}",
                        f"https://www.coursera.org/{subject}",
                        f"https://www.youtube.com/results?search_query={subject}+tutorials"
                    ],
                    "allow_topic_input": allow_topic_input
                })
            elif mark < 75:
                recommendations.append({
                    "subject": subject.capitalize(),
                    "message": f"Your marks in {subject.capitalize()} are decent, but there's room for improvement.",
                    "resources": [
                        f"https://www.edx.org/{subject}",
                        f"https://www.udemy.com/{subject}",
                        f"https://www.skillshare.com/search?query={subject}"
                    ],
                    "allow_topic_input": allow_topic_input
                })
            else:
                recommendations.append({
                    "subject": subject.capitalize(),
                    "message": f"Excellent performance in {subject.capitalize()}! Keep up the great work.",
                    "resources": [
                        f"https://www.ted.com/topics/{subject}",
                        f"https://www.masterclass.com/search?q={subject}"
                    ],
                    "allow_topic_input": allow_topic_input
                })

        return render_template("recommendations.html", recommendations=recommendations)
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for("performance_entry_page"))

# Update existing marks
@app.route("/update-marks/<mark_id>", methods=["POST"])
@login_required
def update_marks(mark_id):
    username = session['username']
    updated_marks = {
        "subject1": int(request.form.get("subject1", 0)),
        "subject2": int(request.form.get("subject2", 0)),
        "subject3": int(request.form.get("subject3", 0)),
        "subject4": int(request.form.get("subject4", 0)),
        "subject5": int(request.form.get("subject5", 0)),
    }
    # Update marks in the database
    marks_collection.update_one(
        {"_id": ObjectId(mark_id), "username": username},
        {"$set": {"marks": updated_marks}}
    )
    return redirect(url_for("visual_representation_page"))

# Delete marks
@app.route("/delete-marks/<mark_id>", methods=["POST"])
@login_required
def delete_marks(mark_id):
    username = session['username']
    # Delete marks from the database
    marks_collection.delete_one({"_id": ObjectId(mark_id), "username": username})
    return redirect(url_for("visual_representation_page"))

# Serve visual-representation-page.html with marks data
@app.route("/visual-representation-page")
@login_required
def visual_representation_page():
    username = session['username']
    try:
        # Retrieve all marks for the logged-in user
        user_marks = marks_collection.find({"username": username})
        marks_list = [{"id": str(mark["_id"]), "marks": mark["marks"]} for mark in user_marks]
        return render_template("visual-representation-page.html", marks=marks_list)
    except Exception as e:
        flash(f"An error occurred while retrieving marks: {str(e)}")
        return redirect(url_for("main_page"))

# API endpoint to get user marks
@app.route('/api/get-user-marks', methods=['GET'])
@login_required
def get_user_marks():
    username = session['username']
    user_marks = marks_collection.find_one({"username": username})
    if user_marks and "marks" in user_marks:
        return jsonify({"marks": list(user_marks["marks"].values())})
    return jsonify({"marks": [0, 0, 0, 0, 0]})

# API endpoint to get all marks for visualization
@app.route('/api/get-all-marks', methods=['GET'])
@login_required
def get_all_marks():
    username = session['username']
    user_marks = marks_collection.find({"username": username})
    marks_list = [{"id": str(mark["_id"]), "marks": mark["marks"]} for mark in user_marks]
    return jsonify({"marks": marks_list})

@app.route("/recommendations")
@login_required
def recommendations():
    username = session['username']
    try:
        # Retrieve all marks for the logged-in user
        user_marks = list(marks_collection.find({"username": username}))
        if not user_marks:
            flash("No marks data available. Please enter marks first.")
            return redirect(url_for("performance_entry_page"))

        # Aggregate marks to calculate average performance per subject
        subject_totals = {"math": 0, "science": 0, "social": 0, "computer": 0, "gk": 0}
        subject_counts = {"math": 0, "science": 0, "social": 0, "computer": 0, "gk": 0}

        for mark_entry in user_marks:
            for subject, mark in mark_entry["marks"].items():
                subject_totals[subject] += mark
                subject_counts[subject] += 1

        # Calculate average marks for each subject
        subject_averages = {
            subject: (subject_totals[subject] / subject_counts[subject])
            for subject in subject_totals
            if subject_counts[subject] > 0
        }

        recommendations = []

        # Generate recommendations based on average marks
        for subject, avg_mark in subject_averages.items():
            if avg_mark < 35:
                recommendations.append({
                    "subject": subject.capitalize(),
                    "message": f"Your average marks in {subject.capitalize()} are below 35. Focus on improving this subject.",
                    "resources": [
                        f"https://www.khanacademy.org/{subject}",
                        f"https://www.coursera.org/{subject}",
                        f"https://www.youtube.com/results?search_query={subject}+tutorials"
                    ]
                })
            elif avg_mark < 75:
                recommendations.append({
                    "subject": subject.capitalize(),
                    "message": f"Your average marks in {subject.capitalize()} are decent, but there's room for improvement.",
                    "resources": [
                        f"https://www.edx.org/{subject}",
                        f"https://www.udemy.com/{subject}",
                        f"https://www.skillshare.com/search?query={subject}"
                    ]
                })
            else:
                recommendations.append({
                    "subject": subject.capitalize(),
                    "message": f"Excellent performance in {subject.capitalize()}! Keep up the great work.",
                    "resources": [
                        f"https://www.ted.com/topics/{subject}",
                        f"https://www.masterclass.com/search?q={subject}"
                    ]
                })

        return render_template("recommendations.html", recommendations=recommendations)
    except Exception as e:
        flash(f"An error occurred while generating recommendations: {str(e)}")
        return redirect(url_for("main_page"))

@app.route("/logout")
def logout():
    session.clear()  # Clear the session to log out the user
    flash("You have been logged out successfully.")
    return redirect(url_for("login"))

@app.route('/fetch-resources', methods=['POST'])
def fetch_resources():
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')

    if not subject or not topic:
        return jsonify({"error": "Subject and topic are required"}), 400

    # Use an external API to fetch relevant resources
    # Example: Using Bing Search API (replace with your API key and endpoint)
    api_key = "your_bing_api_key"  # Replace with your Bing Search API key
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    query = f"{subject} {topic} resources"

    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": 5}  # Limit to 5 results

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        search_results = response.json()

        # Extract relevant links and titles from the search results
        resources = [
            {"title": item["name"], "url": item["url"]}
            for item in search_results.get("webPages", {}).get("value", [])
        ]

        return jsonify({"resources": resources})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch resources: {str(e)}"}), 500

@app.route('/all-marks')
@login_required
def all_marks():
    username = session['username']
    try:
        # Retrieve all marks for the logged-in user
        user_marks = marks_collection.find({"username": username})
        marks_list = [
            {"id": str(mark["_id"]), "marks": mark["marks"]}
            for mark in user_marks
        ]
        return render_template('all-marks.html', marks=marks_list)
    except Exception as e:
        flash(f"An error occurred while retrieving marks: {str(e)}")
        return redirect(url_for("main_page"))

@app.route('/delete-mark/<mark_id>', methods=['POST'])
@login_required
def delete_mark(mark_id):
    username = session['username']
    try:
        # Delete the specific mark entry from the database
        result = marks_collection.delete_one({"_id": ObjectId(mark_id), "username": username})
        if result.deleted_count > 0:
            flash("Mark entry deleted successfully.")
        else:
            flash("Failed to delete the mark entry.")
    except Exception as e:
        flash(f"An error occurred while deleting the mark entry: {str(e)}")
    return redirect(url_for('all_marks'))

if __name__ == "__main__":
    app.run(debug=True)
