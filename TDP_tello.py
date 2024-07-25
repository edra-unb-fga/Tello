from djitellopy import Tello
import cv2
import mediapipe as mp
import os
import time
import threading

# Suprime avisos do TensorFlow Lite
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Inicializa o MediaPipe para reconhecimento de mãos
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Função para conectar ao drone Tello com tentativas de reconexão
def connect_tello():
    tello = Tello()
    while True:
        try:
            tello.connect()
            tello.streamon()  # Ativa o stream de vídeo
            print("Conectado ao Tello")
            return tello
        except Exception as e:
            print(f"Erro ao conectar ao Tello: {e}")
            print("Tentando reconectar em 5 segundos...")
            time.sleep(5)

# Conecta ao drone Tello
tello = connect_tello()
print("Decolar")
tello.takeoff()
tello.move_up(40)

# Variável para verificar se o comando terminou
command_is_over = True
current_gesture = None

# Função para detectar gestos
def detect_gesture(landmarks):
    if landmarks:
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        # Detecta o gesto de subir (indicador levantado)
        if index_tip.y < thumb_tip.y and middle_tip.y > thumb_tip.y and ring_tip.y > thumb_tip.y and pinky_tip.y > thumb_tip.y:
            return "move_up"
        
        # Detecta o gesto de descer (indicador e médio levantados)
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
        
        # Detecta o gesto de mover para frente (indicador e mindinho levantados)
        if index_tip.y < thumb_tip.y and middle_tip.y > thumb_tip.y and ring_tip.y > thumb_tip.y and pinky_tip.y < thumb_tip.y:
            return "move_forward"
        
        # Detecta o gesto de mover para trás (thumb longe do indicador no eixo x)
        if abs(thumb_tip.x - index_tip.x) > 0.2:  # Ajuste o valor conforme necessário
            return "move_backward"
        
        # Detecta o gesto de pousar definitivamente (apenas o mindinho levantado)
        if index_tip.y > thumb_tip.y and middle_tip.y > thumb_tip.y and ring_tip.y > thumb_tip.y and pinky_tip.y < thumb_tip.y:
            return "land and takeoff"
    
    return None

# Funções de controle do Tello
def move_up():
    print("Subir")
    response = tello.send_command_with_return("up 20")
    print(f"Resposta do drone: {response}")
    return response

def move_down():
    print("Descer")
    response = tello.send_command_with_return("down 20")
    print(f"Resposta do drone: {response}")
    return response

def rotate_left():
    print("Rotacionar para a esquerda")
    response = tello.send_command_with_return("ccw 90")
    print(f"Resposta do drone: {response}")
    return response

def rotate_right():
    print("Rotacionar para a direita")
    response = tello.send_command_with_return("cw 90")
    print(f"Resposta do drone: {response}")
    return response

def move_forward():
    print("Mover para frente")
    response = tello.send_command_with_return("forward 40")
    print(f"Resposta do drone: {response}")
    return response

def move_backward():
    print("Mover para trás")
    response = tello.send_command_with_return("back 40")
    print(f"Resposta do drone: {response}")
    return response

def land():
    print("Pousar")
    response = tello.send_command_with_return("land")
    print(f"Resposta do drone: {response}")
    return response

def execute_command(gesture):
    global command_is_over
    if gesture == "move_up":
        command_is_over = move_up() == "ok"
    elif gesture == "move_down":
        command_is_over = move_down() == "ok"
    elif gesture == "rotate_left":
        command_is_over = rotate_left() == "ok"
    elif gesture == "rotate_right":
        command_is_over = rotate_right() == "ok"
    elif gesture == "move_forward":
        command_is_over = move_forward() == "ok"
    elif gesture == "move_backward":
        command_is_over = move_backward() == "ok"
    elif gesture == "land and takeoff":
        command_is_over = land() == "ok"
        time.sleep(5)
        tello.takeoff()
        tello.send_command_without_return('up 60')
    elif gesture == "land":
        command_is_over = land() == "ok"
        
# Loop principal para capturar o vídeo do Tello
while True:
    frame = tello.get_frame_read().frame
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = detect_gesture(hand_landmarks.landmark)

            if gesture and command_is_over:
                print(f"Ação detectada: {gesture}")
                cv2.putText(frame, f'Status: {gesture}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                command_is_over = False  # Bloqueia novos comandos até o comando atual ser concluído
                current_gesture = gesture
                threading.Thread(target=execute_command, args=(gesture,)).start()

    battery = tello.get_battery()
    print("Bateria:", battery, "%")
    cv2.putText(frame, f'Bateria: {battery}%', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Image", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

tello.streamoff()
cv2.destroyAllWindows()

# Desconecta o drone Tello
tello.end()


