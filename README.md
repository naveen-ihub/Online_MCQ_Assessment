
# **Online MCQ Assessment**

The Online MCQ Assessment is a web-based platform for managing and taking multiple-choice quizzes. It allows hosts to create and manage tests while providing candidates a seamless interface to register, take tests, and view results.

---

## **Features**

### Host Dashboard
- Create, edit, and delete quizzes.
- Select topics and manage questions.
- Monitor hosted tests.

### Candidate Dashboard
- Register and log in securely.
- View available tests and track test statuses.
- Take quizzes within the scheduled time.

### Authentication
- Secure user sessions with registration and login functionality.

---

## **Tech Stack**
- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript

---

## **Prerequisites**
- **Python**: Ensure Python 3.8 or higher is installed.
- **MongoDB**: Install MongoDB locally or use a MongoDB cloud instance.
- **Libraries**: Flask, PyMongo (listed in `requirements.txt`).

---

## **Installation**

### Step 1: Clone the Repository
```bash
git clone <repository_url>
cd <repository_directory>
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```
(Dependencies include Flask and PyMongo.)

### Step 3: Configure MongoDB
Update the MongoDB connection URI in the Flask application (`app.py`):
```python
client = pymongo.MongoClient("<your_mongo_connection_uri>")
```

### Step 4: Run the Application
Start the Flask application:
```bash
python app.py
```

---

## **Running the Application**

1. Open your web browser.
2. Navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## **Usage**

### For Hosts:
1. Register or log in.
2. Create quizzes, manage questions, and track tests.
3. View, edit, or delete hosted tests.

### For Candidates:
1. Register or log in from the "Candidate Home" section.
2. View available tests on the dashboard.
3. Start tests within their scheduled time.

settings and requirements.
