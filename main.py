import webbrowser
from pathlib import Path

import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from robothand import RobotHand

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1, detectionCon=0.7)
robot = RobotHand()

if not robot.connected:
    webbrowser.open(Path("viewer/robot_hand.html").resolve().as_uri()) 

# Landmark IDs for each finger (base → tip)
FINGERS = {
    "thumb":  [1, 2, 3, 4],
    "index":  [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring":   [13, 14, 15, 16],
    "pinky":  [17, 18, 19, 20],
}


def bendAngle(a, b, c):
    """Angle at point b in degrees. 0 = straight."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    v1, v2 = b - a, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


while True:
    ok, img = cap.read()
    if not ok:
        break
    img = cv2.flip(img, 1)

    hands, img = detector.findHands(img)
    if hands:
        lm = hands[0]["lmList"]  # 21 points [x, y, z]

        for name, (p1, p2, p3, p4) in FINGERS.items():
            a1 = bendAngle(lm[0], lm[p1], lm[p2])  # knuckle (from wrist)
            a2 = bendAngle(lm[p1], lm[p2], lm[p3])  # middle
            a3 = bendAngle(lm[p2], lm[p3], lm[p4])  # tip
            robot.setFinger(name, a1, a2, a3)

        robot.update()

    cv2.imshow("Webcam", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
