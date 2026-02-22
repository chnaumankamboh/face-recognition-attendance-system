import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-e6ac1-default-rtdb.firebaseio.com/"
})


ref = db.reference('Students')

data = {
    "6046":
        {
            "name": "Nauman Saleem",
            "major": "Robotics",
            "Present": 3,
            "Absent": 2,
            'last_attendance_time': "2025-12-30 00:54:34",
            "daily_attendance": {}
        },

    "6039":
        {
            "name": "Aqsa Mumtaz",
            "major": "Computer Science",
            "Present": 1,
            "Absent": 0,
            'last_attendance_time': "2025-12-30 00:54:34",
            "daily_attendance": {}
        },

    "6040":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "Present": 0,
            "Absent": 0,
            'last_attendance_time': "2025-12-30 00:54:34",
            "daily_attendance": {}
        }
}

for key, value in data.items():
    ref.child(key).set(value)