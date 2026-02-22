import cv2
import os
import face_recognition
import pickle

folderPath = 'Images'
pathList = os.listdir(folderPath)
imgList = []
studentIds = []
imagePaths = []

for path in pathList:
    fullPath = os.path.join(folderPath, path)
    imgList.append(cv2.imread(fullPath))
    studentIds.append(os.path.splitext(path)[0])
    imagePaths.append(fullPath)   # 👈 pointer to image

    #print(os.path.splitext(path)[0])
print(studentIds)

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

print("Encoding Started...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown,studentIds,imagePaths]
print("Encoding Complete")

file = open('EncodeFile.p','wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File Save")