import cv2
import numpy as np
from djitellopy import Tello
import time
import mediapipe as mp
import tkinter as tk

tello = Tello()
tello.connect()
print(tello.get_battery())

tello.streamon()
tello.takeoff()
tello.send_rc_control(0, 0, 5, 0)
time.sleep(1)

w, h = 720, 720
fbRange = [6200, 6800]
pid = [0.4, 0.4, 0]
pError = 0

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Criar janela de status
root = tk.Tk()
root.title("Status do Drone")
status_label = tk.Label(root, text="Status: ", font=("Helvetica", 16))
status_label.pack(pady=20)

def update_status(message):
    status_label.config(text=f"Status: {message}")
    root.update()

def detect_gesture(landmarks):
    if landmarks:
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        # Detecta o gesto de decolagem (todos os dedos levantados)
        if thumb_tip.y < index_tip.y and thumb_tip.y < middle_tip.y and thumb_tip.y < ring_tip.y and thumb_tip.y < pinky_tip.y:
            return "takeoff"
        
        # Detecta o gesto de subir 5 cm (indicador levantado)
        if index_tip.y < thumb_tip.y and middle_tip.y > thumb_tip.y and ring_tip.y > thumb_tip.y and pinky_tip.y > thumb_tip.y:
            return "move_up"
        
        # Detecta o gesto de descer 5 cm (indicador e médio levantados)
        if index_tip.y < thumb_tip.y and middle_tip.y < thumb_tip.y and ring_tip.y > thumb_tip.y and pinky_tip.y > thumb_tip.y:
            return "move_down"
        
        # Detecta o gesto para girar para a esquerda (indicador, médio e anelar levantados)
        if index_tip.y < thumb_tip.y and middle_tip.y < thumb_tip.y and ring_tip.y < thumb_tip.y and pinky_tip.y > thumb_tip.y:
            return "rotate_left"
        
        # Detecta o gesto para girar para a direita (indicador, médio, anelar e mindinho levantados)
        if index_tip.y < thumb_tip.y and middle_tip.y < thumb_tip.y and ring_tip.y < thumb_tip.y and pinky_tip.y < thumb_tip.y:
            return "rotate_right"
        
        # Detecta o gesto de pouso (todos os dedos abaixados)
        if index_tip.y > thumb_tip.y and middle_tip.y > thumb_tip.y and ring_tip.y > thumb_tip.y and pinky_tip.y > thumb_tip.y:
            return "land"
    
    return None

def move_up():
    height = tello.get_height()
    print(f"Current height: {height} cm")
    if height < 1000:  # assumindo que a altura máxima é 1000 cm (10 metros)
        print("Subir 5 cm")
        tello.move_up(5)
    else:
        print("Altura máxima atingida")

def move_down():
    height = tello.get_height()
    print(f"Current height: {height} cm")
    if height > 5:  # garantindo que está acima do solo
        print("Descer 5 cm")
        tello.move_down(5)
    else:
        print("Altura mínima atingida")

def rotate_left():
    print("Rotacionar para a esquerda")
    tello.rotate_counter_clockwise(90)

def rotate_right():
    print("Rotacionar para a direita")
    tello.rotate_clockwise(90)

def land():
    print("Pousar")
    tello.land()

def findFace(img):
    faceCascade = cv2.CascadeClassifier("Resources/haarcascade_frontalface_default.xml")
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(imgGray, 1.2, 8)

    myFaceListC = []
    myFaceListArea = []

    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cx = x + w // 2
        cy = y + h // 2
        area = w * h
        cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
        myFaceListC.append([cx, cy])
        myFaceListArea.append(area)

    if len(myFaceListArea) != 0:
        i = myFaceListArea.index(max(myFaceListArea))
        return img, [myFaceListC[i], myFaceListArea[i]]
    else:
        return img, [[0, 0], 0]

def trackFace(info, w, pid, pError):
    area = info[1]
    x, y = info[0]
    fb = 0

    error = x - w // 2
    speed = pid[0] * error + pid[1] * (error - pError)
    speed = int(np.clip(speed, -100, 100))

    if area > fbRange[0] and area < fbRange[1]:
        fb = 0
    elif area > fbRange[1]:
        fb = -20
    elif area < fbRange[0] and area != 0:
        fb = 20

    if x == 0:
        speed = 0
        error = 0

    tello.send_rc_control(0, fb, 0, speed)
    return error

while True:
    img = tello.get_frame_read().frame
    img = cv2.resize(img, (w, h))
    img, info = findFace(img)
    #pError = trackFace(info, w, pid, pError)
    
    # Processamento de gestos
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = detect_gesture(hand_landmarks.landmark)
            if gesture == "move_up":
                update_status("Subindo....") #um dedo
                # move_up()
            elif gesture == "move_down":
                update_status("Descendo....") # dois dedos
                # move_down()
            elif gesture == "rotate_left":
                update_status("Esquerda....") #tres dedos
                # rotate_left()
            elif gesture == "rotate_right":
                update_status("Direita....")#todos os dedos
                # rotate_right()
            elif gesture == "land":
                update_status("Pousando....")#nenhum dedo
                #land()
    
    cv2.imshow("Output", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        tello.land()
        break

# Executar a janela de status do Tkinter
root.mainloop()

