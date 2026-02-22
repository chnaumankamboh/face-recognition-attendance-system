import os
import pickle
import cv2
import face_recognition
import cvzone
import numpy as np
import time
from datetime import datetime
import calendar

from EncodeGenerator import studentIds
from ExcelManager import update_attendance_sheet


import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-e6ac1-default-rtdb.firebaseio.com/",
})

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

imgBackground = cv2.imread('Resources/Background2.png')
classOverview = cv2.imread('Resources/classOverview/classOverviewbackground2.png')

current_date = datetime.now()
year = current_date.year
month = current_date.month
daysInTheMonth = calendar.monthrange(year, month)[1]

# student details area
studentDetailsPaths = os.listdir('Resources/StudentDetailsArea')
studentDetailsList = [cv2.imread(os.path.join('Resources/StudentDetailsArea', path)) for path in studentDetailsPaths]

folderModePath = 'Resources/StudentDetailsArea'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath,path)))
#print(len(imgModeList))

# loading encoded file
print("Loading Encode File...")
file = open('EncodeFile.p','rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, StudentIds , imagePaths = encodeListKnownWithIds
#print(studentIds)
print("Loading Encode File Loaded")

modeType = 0
counter = 0
id = -1
studentImage =  []
lastDetectionTime = 0
ref = db.reference(f"Students/{id}")
studentInfo = db.reference(f'Students/{id}').get()
allStudentInformation = db.reference(f"Students").get()
# Firebase fetch control (prevents lag)
firebase_refresh_interval = 5  # seconds
last_firebase_fetch = 0

while True:
    currentTime = time.time()
    success, img = cap.read()

    imgS = cv2.resize(img, (0,0), None, fx= 0.25, fy= 0.25,interpolation = cv2.INTER_AREA)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)


    imgSmall = cv2.resize(img, (320, 240))
    imgBackground[10:10 + 240, 1270 - 320:1270] = imgSmall
    imgBackground[10:10 + 700, 10:10 + 426] = imgModeList[modeType]
    imgBackground[10:10 + 700, 426 + 30:426 + 30 + 427] = classOverview

    if faceCurFrame :

        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            #print("Matches: ",matches)
            #print("Difference: ", faceDis)
            minDistance = np.min(faceDis)

            matchIndex = np.argmin(faceDis)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2

            xOffset = 950
            yOffset = 10
            bbox = (
                xOffset + x1,
                yOffset + y1,
                x2 - x1,
                y2 - y1
            )

            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

            if minDistance >= 0.5:
                counter = 0
                modeType = 3
                continue

            # DISTANCE THRESHOLD
            if matches[matchIndex] and faceDis[matchIndex] <= 0.5:
                studentImagePath = imagePaths[matchIndex]
                studentImage = cv2.imread(studentImagePath)

                id = studentIds[matchIndex]

                if counter ==0:
                    cvzone.putTextRect(imgBackground,"Loading",(1110,130),
                                       scale=1,thickness=1)
                    cv2.imshow("Face Attendance",imgBackground)
                    cv2.waitKey(1)
                    counter =1
                    modeType = 1

            if counter != 0:
                if counter == 1:
                    ref = db.reference(f"Students/{id}")
                    studentInfo = ref.get()

                    current_date_str = datetime.now().strftime("%Y-%m-%d")

                    today_status = studentInfo.get("daily_attendance", {}).get(current_date_str)

                    if today_status == "present":
                        # 🔒 Attendance already taken today
                        modeType = 2
                        counter = 0

                    else:
                        # ✅ Mark attendance for today
                        studentInfo['Present'] += 1

                        studentInfo.setdefault('daily_attendance', {})[
                            current_date_str
                        ] = "present"

                        ref.child('Present').set(studentInfo['Present'])
                        ref.child('daily_attendance').set(studentInfo['daily_attendance'])
                        ref.child('last_attendance_time').set(
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )

                        update_attendance_sheet(
                            roll_no=id,
                            name=studentInfo['name'],
                            date=current_date_str,
                            status="Present"
                        )

                        modeType = 1

                        imgBackground[10:10 + 700, 10:10 + 426] = imgModeList[modeType]

                    name = studentInfo['name']  # type: ignore
                    roll_no = id
                    Presents = studentInfo['Present']  # type: ignore
                    Absents = studentInfo['Absent']  # type: ignore
                    if Absents != 0 or Presents != 0:
                        Percentage = Presents / (Presents + Absents) * 100
                        Percentage = round(Percentage, 2)


                if 10 < counter < 40:
                    modeType = 2

                imgBackground[10:10 + 700, 10:10 + 426] = imgModeList[modeType]
                studentImage = cv2.resize(studentImage, (151, 151))
                imgBackground[80:80 + 151, 20:20 + 151] = studentImage

                cv2.putText(imgBackground, str(name), (30, 59 + 151 + 70), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 0), 1)
                cv2.putText(imgBackground, str(roll_no), (30, 59 + 151 + 140), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 1)
                cv2.putText(imgBackground, str(Presents), (426 - 128, 720 - (59 * 3)), cv2.FONT_HERSHEY_COMPLEX,0.9, (0, 0, 0), 1)
                cv2.putText(imgBackground, str(Absents), (426 - 128, 720 - (59 * 2) + 10), cv2.FONT_HERSHEY_COMPLEX, 0.9, (0, 0, 0), 1)
                cv2.putText(imgBackground, f"{Percentage} %", (426 - 128, 720 - (59) + 20), cv2.FONT_HERSHEY_COMPLEX, 0.9, (0, 0, 0), 1)
                cv2.putText(imgBackground,datetime.now().date().strftime("%d/%m/%Y"),(1280 - 270, 310),cv2.FONT_HERSHEY_DUPLEX,1,(100, 30, 30),1,cv2.LINE_AA)

                counter +=1

                if counter >=40:
                    counter = 0
                    modeType = 0
                    studentImage = []
                    id = -1
                    imgBackground[10:10 + 700, 10:10 + 426] = imgModeList[modeType]

    else:
        modeType = 0
        counter = 0

    # Display date
    cv2.putText(imgBackground, datetime.now().date().strftime("%d/%m/%Y"), (1280 - 270, 310),
                cv2.FONT_HERSHEY_DUPLEX, 1, (100, 30, 30), 1, cv2.LINE_AA)

    # Fetch latest students from Firebase
    # Fetch latest students from Firebase (only every few seconds)
    if time.time() - last_firebase_fetch > firebase_refresh_interval:
        allStudentInformation = db.reference("Students").get()
        last_firebase_fetch = time.time()

    yIncrement = 0
    current_date_str = datetime.now().strftime("%Y-%m-%d")

    for student_id, data in allStudentInformation.items():

        # 🔒 Only allow numeric student IDs
        if not student_id.isdigit():
            continue

        if not isinstance(data, dict):
            continue

        today_attendance = data.get('daily_attendance', {}).get(current_date_str, "Absent")
        text = f"{student_id}                                 {today_attendance.capitalize()}"

        color = (0, 0, 0)
        if today_attendance == 'Absent':
            color = (100, 100, 150)

        cv2.putText(imgBackground,text,(427 + 50, 60 + 40 + 43 + yIncrement),
            cv2.FONT_HERSHEY_COMPLEX,0.5,color,1,cv2.LINE_AA)
        yIncrement += 32

        status = data.get('daily_attendance', {}).get(current_date_str, "Absent")
        update_attendance_sheet(
            roll_no=int(student_id),
            name=data.get("name", "Unknown"),
            date=current_date_str,
            status=status
        )

    cv2.imshow("Face Attendance",imgBackground)
    if cv2.waitKey(1) & 0xFF == (ord('q') or ord('Q')):
        break
    #cv2.imshow("WebCam",img)
    cv2.waitKey(1)