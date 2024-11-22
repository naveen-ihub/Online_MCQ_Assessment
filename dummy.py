from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import csv
import io
from flask import render_template
from bson import ObjectId
from io import StringIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["test_platform_db"]
questions_collection = db["questions"]
# Collections
users_collection = db["users"]
host_collection = db["hosts_test"]
# candidate_collection = db["candidate_test"]
registrations_collection = db['candidate_test']  # Collection to store user registrations




# Route for role selection
@app.route("/")
def select_role():
    return render_template("select_role.html")


# Route for login
@app.route("/login/<user_type>", methods=["GET", "POST"])
def login(user_type):
    if request.method == "POST":
        # Get login credentials
        username = request.form["username"]
        password = request.form["password"]

        # Find user in the database
        user = users_collection.find_one(
            {"username": username, "password": password, "user_type": user_type}
        )

        if user:
            session["username"] = username
            session["user_type"] = user_type
            if user_type == "host":
                return redirect(url_for("host_dashboard"))
            else:
                return redirect(url_for("candidate_home", user_type=user_type))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html", user_type=user_type)


# Route for registration
@app.route("/register/<user_type>", methods=["GET", "POST"])
def register(user_type):
    if request.method == "POST":
        # Get registration details
        username = request.form["username"]
        password = request.form["password"]

        # Check if the username already exists
        if users_collection.find_one({"username": username, "user_type": user_type}):
            flash("Username already exists. Please choose a different one.", "warning")
        else:
            # Save user to the database
            users_collection.insert_one(
                {"username": username, "password": password, "user_type": user_type}
            )
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login", user_type=user_type))

    return render_template("register.html", user_type=user_type)


@app.route("/home/<user_type>")
def home(user_type):
    return f"Welcome to the {user_type.capitalize()} dashboard!"




@app.route("/view_topic/<topic_title>")
def view_topic(topic_title):
    # Fetch the topic document based on topic_title
    topic = db.questions.find_one(
        {"topic_title": topic_title, "username": session.get("username")}
    )

    if topic:
        # Pass the topic data, including the questions array, to the template
        return render_template(
            "view_topic.html", topic=topic, questions=topic.get("questions", [])
        )
    else:
        # Redirect or show an error if the topic is not found
        return redirect(url_for("create_topic"))


@app.route("/edit_question/<topic_title>/<question_id>", methods=["GET", "POST"])
def edit_question(topic_title, question_id):
    # Fetch the topic from the database
    topic = questions_collection.find_one(
        {"topic_title": topic_title, "username": session.get("username")}
    )

    if not topic:
        return redirect(
            url_for("create_topic")
        )  # If topic is not found, redirect back to create topic page

    # Find the specific question to edit
    question_to_edit = None
    for question in topic["questions"]:
        if str(question["_id"]) == question_id:
            question_to_edit = question
            break

    if not question_to_edit:
        return redirect(
            url_for("view_topic", topic_title=topic_title)
        )  # Redirect if question not found

    if request.method == "POST":
        # Handle form submission to update the question
        updated_question = request.form["question"]
        updated_options = {
            "option_a": request.form["option_a"],
            "option_b": request.form["option_b"],
            "option_c": request.form["option_c"],
            "option_d": request.form["option_d"],
        }
        updated_correct_answer = request.form["correct_answer"]

        # Update the question in the database
        topic["questions"] = [
            (
                q
                if str(q["_id"]) != question_id
                else {
                    **q,
                    "question": updated_question,
                    "options": updated_options,
                    "correct_answer": updated_correct_answer,
                }
            )
            for q in topic["questions"]
        ]

        # Save the updated topic back to the database
        questions_collection.save(topic)

        return redirect(
            url_for("view_topic", topic_title=topic_title)
        )  # Redirect back to the topic view page

    # Render the edit question page with the current question details
    return render_template(
        "edit_question.html", topic_title=topic_title, question=question_to_edit
    )


@app.route("/upload_csv/<topic_title>", methods=["POST"])
def upload_csv(topic_title):
    if "csv_file" not in request.files:
        flash("No file part")
        return redirect(url_for("upload_or_add_questions", topic_title=topic_title))

    file = request.files["csv_file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("upload_or_add_questions", topic_title=topic_title))

    # Process CSV file
    if file and file.filename.endswith(".csv"):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)

        questions = []
        for row in reader:
            questions.append(
                {
                    "question": row.get("Question"),
                    "options": [
                        row.get("Option A"),
                        row.get("Option B"),
                        row.get("Option C"),
                        row.get("Option D"),
                    ],
                    "correct_answer": row.get("Correct Answer"),
                }
            )

        # Update topic with questions in the database
        questions_collection.update_one(
            {"topic_title": topic_title, "username": session.get("username")},
            {"$push": {"questions": {"$each": questions}}},
        )

        flash("Questions uploaded successfully!")
        return redirect(url_for("create_topic"))

    flash("Invalid file format. Please upload a CSV file.")
    return redirect(url_for("upload_or_add_questions", topic_title=topic_title))


@app.route("/submit_questions", methods=["POST"])
def submit_questions():
    topic_title = request.form.get("topic_title")
    questions = request.form.getlist("questions")

    # Parse JSON-like structure to insert in DB
    for question in questions:
        questions_collection.insert_one(
            {
                "topic_title": topic_title,
                "username": session.get("username"),
                **question,
            }
        )

    # Redirect to the create topic page after storing in DB
    return redirect(url_for("create_topic"))


@app.route("/create_topic", methods=["GET"])
def create_topic():
    search_term = request.args.get(
        "search"
    )  # Get the search term from the query parameters

    # Handle None search term and assign an empty string if it is None
    if search_term is None:
        search_term = ""

    # If there is a search term, perform a case-insensitive search
    if search_term:
        topics = list(
            questions_collection.find(
                {
                    "topic_title": {"$regex": search_term, "$options": "i"},
                    "username": session.get("username"),
                }
            )
        )
    else:
        # Retrieve all topics if no search term is provided
        topics = list(questions_collection.find({"username": session.get("username")}))

    # If no topics are found, display a 'No topics found' message
    if not topics:
        message = "No topics found!"
    else:
        message = None

    return render_template(
        "create_topic.html", topics=topics, search_term=search_term, message=message
    )


# Route for uploading questions from CSV
@app.route("/upload_or_add_questions", methods=["GET", "POST"])
def upload_or_add_questions():
    if request.method == "POST":
        topic_title = request.form.get("topic_title")

        # Check if the topic already exists in the database
        existing_topic = questions_collection.find_one(
            {"topic_title": topic_title, "username": session.get("username")}
        )

        if existing_topic:
            # If topic exists, display an error message and keep the modal open
            message = f"The topic titled '{topic_title}' already exists!"
            return render_template("upload_or_add_questions.html", message=message)

        # Insert a new topic into the database
        questions_collection.insert_one(
            {"topic_title": topic_title, "username": session.get("username")}
        )

        # Handle CSV file upload
        if "csv_file" in request.files:
            csv_file = request.files["csv_file"]
            if csv_file.filename != "":
                # Read the uploaded CSV file
                file_stream = StringIO(csv_file.read().decode("utf-8"))
                csv_reader = csv.DictReader(file_stream)

                # Process the CSV file and prepare questions to insert into the database
                new_questions = []
                for row in csv_reader:
                    question = row["Question"]
                    options = {
                        "option_a": row["Option A"],
                        "option_b": row["Option B"],
                        "option_c": row["Option C"],
                        "option_d": row["Option D"],
                    }
                    correct_answer = row["Correct Answer"]

                    # Create the new question object
                    new_question = {
                        "question": question,
                        "options": options,
                        "correct_answer": correct_answer,
                    }
                    new_questions.append(new_question)

                # Update the topic with the new questions
                questions_collection.update_one(
                    {"topic_title": topic_title, "username": session.get("username")},
                    {"$push": {"questions": {"$each": new_questions}}},
                )

                # Redirect to a different page after successfully uploading the questions
                return redirect(url_for("create_topic"))

    return render_template("upload_or_add_questions.html", message=None)


@app.route("/add_question s/<topic_title>", methods=["GET", "POST"])
def add_questions(topic_title):
    # Retrieve the topic by its title from the database
    topic = questions_collection.find_one(
        {"topic_title": topic_title, "username": session.get("username")}
    )

    if request.method == "POST":
        # Check if the form contains a CSV file
        if "csv_file" in request.files:
            csv_file = request.files["csv_file"]
            if csv_file.filename != "":
                # Read the CSV file
                filename = secure_filename(csv_file.filename)
                file_stream = StringIO(csv_file.read().decode("utf-8"))
                csv_reader = csv.DictReader(file_stream)

                # Process the CSV file and add questions to the database
                new_questions = []
                for row in csv_reader:
                    question = row["Question"]
                    options = {
                        "option_a": row["Option A"],
                        "option_b": row["Option B"],
                        "option_c": row["Option C"],
                        "option_d": row["Option D"],
                    }
                    correct_answer = row["Correct Answer"]

                    # Create the new question object
                    new_question = {
                        "question": question,
                        "options": options,
                        "correct_answer": correct_answer,
                    }
                    new_questions.append(new_question)

                # Update the topic by appending the new questions to the existing questions
                questions_collection.update_one(
                    {
                        "topic_title": topic_title,
                        "username": session.get("username"),
                    },  # Find the topic by title
                    {
                        "$push": {"questions": {"$each": new_questions}}
                    },  # Append new questions
                )

                # Redirect to the create topic page after uploading questions
                return redirect(url_for("create_topic"))

        else:
            # Handle manual question submission (if necessary)
            question = request.form["question"]
            options = {
                "option_a": request.form["option_a"],
                "option_b": request.form["option_b"],
                "option_c": request.form["option_c"],
                "option_d": request.form["option_d"],
            }
            correct_answer = request.form["correct_answer"]

            # Create a new question
            new_question = {
                "question": question,
                "options": options,
                "correct_answer": correct_answer,
            }

            # Append the new question to the existing topic
            questions_collection.update_one(
                {
                    "topic_title": topic_title,
                    "username": session.get("username"),
                },  # Find the topic by title
                {
                    "$push": {"questions": new_question}
                },  # Add the new question to the topic
            )

            # Redirect to the create topic page after adding the question
            return redirect(url_for("create_topic"))

    return render_template("add_questions.html", topic_title=topic_title)


@app.route("/delete_topic/<topic_title>", methods=["GET"])
def delete_topic(topic_title):
    # Delete the topic by its title
    questions_collection.delete_one(
        {"topic_title": topic_title, "username": session.get("username")}
    )
    # questions_collection.delete_one({"topic_title": topic_title})
    return redirect(url_for("create_topic"))


@app.route("/host_test")
def host_test():
    return render_template("host_test.html")


@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    if "username" not in session:
        return redirect(url_for("home"))
    session["quiz_id"] = str(ObjectId())

    quiz_data = {
        "quiz_id": session["quiz_id"],
        "username": session["username"],
        "title": request.form["title"],
        "organization": request.form["organization"],
        "website_url": request.form["website_url"],
        "skills": request.form["skills"],
        "about_test": request.form["about_test"],
        "start_time": request.form["start_time"],
        "end_time": request.form["end_time"],
        "test_duration": request.form["test_duration"],
    }
    host_collection.insert_one(quiz_data)
    return redirect(url_for("topic_choose", quiz_id=quiz_data["_id"]))


@app.route("/topic_choose")
def topic_choose():

    search_term = request.args.get(
        "search"
    )  # Get the search term from the query parameters

    # Handle None search term and assign an empty string if it is None
    if search_term is None:
        search_term = ""

    # If there is a search term, perform a case-insensitive search
    if search_term:
        topics = list(
            questions_collection.find(
                {
                    "topic_title": {"$regex": search_term, "$options": "i"},
                    "username": session.get("username"),
                }
            )
        )
    else:
        # Retrieve all topics if no search term is provided
        topics = list(questions_collection.find({"username": session.get("username")}))

    # If no topics are found, display a 'No topics found' message
    if not topics:
        message = "No topics found!"
    else:
        message = None

    return render_template(
        "topic_choose.html", topics=topics, search_term=search_term, message=message
    )


@app.route("/create_question")
def create_question():
    return render_template("create_question.html")


# Route to submit questions
@app.route("/create_questionpage", methods=["POST"])
def create_questionpage():
    if "username" not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No questions provided"}), 400

    topic_title = data.get("topic_title")

    # Check if the topic already exists in the database
    existing_topic = questions_collection.find_one(
        {"topic_title": topic_title, "username": session.get("username")}
    )

    if existing_topic:
        return (
            jsonify({"error": f"The topic titled '{topic_title}' already exists!"}),
            400,
        )

    # Insert questions into the MongoDB collection
    data["username"] = session.get("username")
    questions_collection.insert_one(data)
    return jsonify({"message": "Questions submitted and saved successfully"}), 200


# Logout route
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("select_role"))

@app.route("/select_question_count", methods=["POST"])
def select_question_count():
    # Retrieve quiz data from MongoDB using the session's quiz_id and username

    selected_topics = request.form.getlist("selected_topics[]")


    # Save the selected topics in the session or process them directly
    session['selected_topics'] = selected_topics

    print(f'selected_topics: {session["selected_topics"]}')   

    host_collection.update_one(
        {"quiz_id": session["quiz_id"], "username": session["username"]},
        {"$set": {"selected_topics": selected_topics}}
    )
    return render_template("question_count.html", selected_topics=selected_topics)


@app.route("/submit_quiz_setup", methods=["POST"])
def submit_quiz_setup():
    data = host_collection.find_one(
        {"quiz_id": session["quiz_id"], "username": session["username"]}
    )
    selected_topics = session['selected_topics']
    # Convert form data to a dictionary
    topic_counts = request.form.to_dict()

    print(f'topic_counts: {topic_counts}')
    temp_dict = {}

    # Process the selected topics and their question counts
    for i, count in enumerate(topic_counts.values()):
        print(f"Topic: {selected_topics[i]}, Question Count: {count}")
        temp_dict[selected_topics[i]] = count

    print(f'temp_dict: {temp_dict}')

    host_collection.update_one(
        {"quiz_id": session["quiz_id"], "username": session["username"]},
        {"$set": {"topic_counts": temp_dict}}
    )
    # Redirect to next step or display results
    return redirect(url_for("host_dashboard"))


# Route for the Host Dashboard
@app.route("/host_dashboard")
def host_dashboard():
    username = session.get("username")  # Assuming you store the username in the session
    if username:
        # Fetch all tests for the logged-in user
        tests = host_collection.find({"username": username})
        print(f'tests: {tests}')
        return render_template("host_dashboard.html", tests=tests)
    else:
        return redirect(url_for("login"))



@app.route("/view_test/<quiz_id>")
def view_test(quiz_id):
    # Find the test by quiz_id
    test = host_collection.find_one({"quiz_id": quiz_id, "username": session.get("username")})
    
    if not test:
        return "Test not found", 404
    
    return render_template("view_test.html", test=test)



@app.route("/delete_test/<quiz_id>")
def delete_test(quiz_id):
    host_collection.delete_one({"quiz_id":quiz_id})
    return redirect(url_for('host_dashboard'))



@app.route("/edit_test/<quiz_id>")
def edit_test(quiz_id):
    test = host_collection.find_one({"quiz_id": quiz_id, "username": session.get("username")})
    return render_template("edit_test.html", test=test)


@app.route("/update_test/<quiz_id>", methods=["POST"])
def update_test(quiz_id):
    # Retrieve the form data from the request
    updated_test = {
        "title": request.form.get("title"),
        "organization": request.form.get("organization"),
        "website_url": request.form.get("website_url"),
        "about_test": request.form.get("about_test"),
        "test_duration": int(request.form.get("test_duration")),
        "start_time": request.form.get("start_time"),
        "end_time": request.form.get("end_time")
    }

    # Find the test and update it in the database
    host_collection.update_one(
        {"quiz_id": quiz_id, "username": session.get("username")},
        {"$set": updated_test}
    )

    flash("Test updated successfully!", "success")

    # Redirect back to the view test page
    return redirect(url_for("view_test", quiz_id=quiz_id))


# Route to display all available tests
@app.route("/candidate_home")
def candidate_home():
    all_tests = host_collection.find()  # Fetch all tests from the database
    return render_template("candidate_home.html", all_tests=all_tests)

# Route to register for a test
@app.route('/register_for_test/<quiz_id>', methods=['GET', 'POST'])
def register_for_test(quiz_id):
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Check if the user is already registered for the test
        existing_registration = registrations_collection.find_one({"email": email, "quiz_id": quiz_id})

        if existing_registration:
            flash("You have already registered for this test!", "warning")
            return redirect(url_for('register_for_test', quiz_id=quiz_id))

        # Hash the password before storing it (for security reasons)
        hashed_password = generate_password_hash(password)

        # Register the user if they haven't registered already
        registration_data = {
            "email": email,
            "username": username,
            "password": hashed_password,
            "quiz_id": quiz_id
        }
        registrations_collection.insert_one(registration_data)
        session['username'] = username
        session['email'] = email

        flash("You have successfully registered for the test!", "success")
        return redirect(url_for('candidate_dashboard'))

    # Handle GET request (to display registration form)
    return render_template('register_test.html', quiz_id=quiz_id)



@app.route("/candidate_dashboard")
def candidate_dashboard():
    username = session.get("username")  # Assuming you have session management
    email = session.get("email")  # Get email from session

    if not username:
        # Redirect to login or another page if session data is not set
        return redirect(url_for('login'))
    
    print(username,email)

    # Get registered tests from MongoDB where both username and email match
    registered_tests = list(registrations_collection.find({"username": username}))

    quiz = [test['quiz_id'] for test in registered_tests]

    registered_tests = host_collection.find({"quiz_id": {"$in": quiz}})

    return render_template("candidate_dashboard.html", registered_tests=registered_tests)



# Route to start the test
@app.route("/start_test/<quiz_id>")
def start_test(quiz_id):
    # Logic for starting the test
    return render_template("confirmation.html", quiz_id=quiz_id)

# Route to start the test
@app.route("/guidelines/<quiz_id>")
def guidelines(quiz_id):
    # Logic for starting the test
    return render_template("guidelines.html", quiz_id=quiz_id)


@app.route("/test_page/<quiz_id>")
def test_page(quiz_id):
    quiz = host_collection.find_one({"quiz_id": quiz_id})
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    
    # Fetch questions from selected topics
    topics = quiz["selected_topics"]
    questions = []
    
    for topic in topics:
        topic_data = questions_collection.find_one({"topic_title": topic})
        if topic_data:
            questions.extend(topic_data['questions'])
        
    data = {
        "title": quiz["title"],
        "test_duration": quiz["test_duration"],  # Duration in minutes
        "questions": questions
    }

    print(f'data: {data}')
    
    return render_template("test_page.html", data=data)





if __name__ == "__main__":
    app.run(debug=True)
