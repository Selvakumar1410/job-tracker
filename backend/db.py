import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="job_tracker_db"
)

cursor = db.cursor(dictionary=True)
