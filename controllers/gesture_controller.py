import cv2
import time
import py_trees
import mediapipe as mp
from typing import Optional

class GestureControl(py_trees.behaviour.Behaviour):
    def __init__(self, name: str = "Controle por Gestos", gui: Optional[object] = None):
        super().__init__(name)
        self.drone = None
        self.mp_hands = mp.solutions.hands
        self.hands = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.gui = gui
        self.last_frame_time = 0.0
        self.frame_count = 0

    def setup(self, **kwargs) -> bool:
        try:
            self.drone = kwargs['drone']
            self.drone.streamon()
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=self.gui.detection_confidence.get()
            )
            return True
        except KeyError as e:
            self.logger.error('setup() deve ser chamado com o argumento "drone"')
            return False

    def update(self) -> py_trees.common.Status:
        current_time = time.time()
        if current_time - self.last_frame_time < 1 / self.gui.frame_rate.get():
            return py_trees.common.Status.RUNNING

        self.frame_count += 1
        if self.frame_count % (self.gui.skip_frames.get() + 1) != 0:
            return py_trees.common.Status.RUNNING

        frame = self.drone.get_frame_read().frame
        if self.gui.resolution.get() != 720:
            frame = cv2.resize(frame, (self.gui.resolution.get() * 16 // 9, self.gui.resolution.get()))

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if self.gui.draw_landmarks.get():
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, _ = frame.shape
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)

                if cy < h // 3:
                    self.drone.move_up(self.gui.move_distance.get())
                elif cy > 2 * h // 3:
                    self.drone.move_down(self.gui.move_distance.get())
                elif cx < w // 3:
                    self.drone.move_left(self.gui.move_distance.get())
                elif cx > 2 * w // 3:
                    self.drone.move_right(self.gui.move_distance.get())
                else:
                    self.drone.send_rc_control(0, 0, 0, 0)

        self.overlay_info(frame)

        cv2.imshow('Controle por Gestos', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return py_trees.common.Status.SUCCESS

        self.last_frame_time = current_time
        return py_trees.common.Status.RUNNING

    def overlay_info(self, frame):
        info = f"FPS: {self.gui.frame_rate.get()} | Res: {self.gui.resolution.get()}p"
        info += f" | Conf: {self.gui.detection_confidence.get():.2f}"
        info += f" | Pular: {self.gui.skip_frames.get()}"
        info += f" | Mover: {self.gui.move_distance.get()}cm"
        cv2.putText(frame, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def terminate(self, new_status: py_trees.common.Status):
        self.drone.streamoff()
        cv2.destroyAllWindows()
