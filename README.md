Online MCQ Assessment:
This project is a web-based test management platform that allows hosts to create quizzes, select topics, and manage questions while candidates can register, take tests, and view results.

Features
Host Dashboard: Create, edit, and delete quizzes; select topics and manage questions.
Candidate Dashboard: Register for quizzes, view available tests, and track test statuses.
Authentication: Secure user sessions with registration and login functionality.
Database: MongoDB used to store quizzes, questions, and user data.

Prerequisites
Python: Ensure Python 3.8 or higher is installed.
MongoDB: Install MongoDB locally or have access to a MongoDB cloud instance.
Libraries: Install dependencies listed in requirements.txt.

Installation Steps
Make sure the folder from the zipfile present in the code platform(vscode) 
Install Dependencies:
bash
Copy code
pip install -r requirements.txt
(flask,pymongo)


Configure MongoDB:
Update the MongoDB connection URI in your Flask application:
python
Copy code
client = pymongo.MongoClient("<Your MongoDB URI>")


Run the Flask Application:
bash
Copy code
python app.py



Running the Application
Open a web browser and navigate to:
arduino
Copy code
http://127.0.0.1:5000


For Hosts:
Register or log in.
Create quizzes, select topics, and manage questions.
View, edit, or delete hosted tests.
For Candidates:
Register for a test using the "Candidate Home" section.
View the dashboard to see registered tests and their statuses.
Start tests within the scheduled time.


