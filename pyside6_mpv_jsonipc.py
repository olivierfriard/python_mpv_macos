import sys
import socket
import json
import subprocess
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QLabel


class MPVWidget(QWidget):
    def __init__(self, socket_path="/tmp/mpvsocket", parent=None):
        super().__init__(parent)
        self.socket_path = socket_path
        self.process = None
        self.sock = None
        self.init_mpv()

    def init_mpv(self):
        """Start mpv process and embed it in the PySide6 application."""

        print("start MPV process")

        print(f"{self.winId()=}")
        print(f"{str(int(self.winId()))=}")

        self.process = subprocess.Popen(
            [
                "mpv",
                "--no-border",
                "--ontop",  # mpv window on top
                "--osc=no",  # no on screen commands
                "--input-ipc-server=" + self.socket_path,
                "--wid=" + str(int(self.winId())),  # Embed in the widget
                "--idle",  # Keeps mpv running with no video
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        print(f"{self.process=}")

    def send_command(self, command):
        """Send a JSON command to the mpv IPC server."""
        try:
            # Create a Unix socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                # Connect to the MPV IPC server
                client.connect(self.socket_path)
                # Send the JSON command
                # print(f"{json.dumps(command).encode('utf-8')=}")
                client.sendall(json.dumps(command).encode("utf-8") + b"\n")
                # Receive the response
                response = client.recv(2000)
                print()
                print(f"{response=}")
                # Parse the response as JSON
                response_data = json.loads(response.decode("utf-8"))
                print(f"{response_data=}")
                # Return the 'data' field which contains the playback position
                return response_data.get("data")
        except FileNotFoundError:
            print("Error: Socket file not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return None

    def load_file(self, file_path) -> None:
        """Load a media file in mpv."""
        self.send_command({"command": ["loadfile", file_path]})
        self.pause()
        self.send_command({"command": ["set_property", "time-pos", 0]})

    def get_position(self):
        return self.send_command({"command": ["get_property", "time-pos"]})

    def pause(self):
        return self.send_command({"command": ["set_property", "pause", True]})


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MPV with PySide6 via JSONIPC")
        self.resize(800, 600)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)

        # MPV Widget
        self.mpv_widget = MPVWidget()
        layout.addWidget(self.mpv_widget)

        hlayout = QHBoxLayout(self.central_widget)

        load_button = QPushButton("Load Video", clicked=self.load_video)
        hlayout.addWidget(load_button)

        play_button = QPushButton("Play", clicked=self.play)
        hlayout.addWidget(play_button)

        pause_button = QPushButton("Pause", clicked=self.pause)
        hlayout.addWidget(pause_button)

        frame_forward_button = QPushButton("frame forward", clicked=self.frame_forward)
        hlayout.addWidget(frame_forward_button)

        frame_backward_button = QPushButton("frame backward", clicked=self.frame_backward)
        hlayout.addWidget(frame_backward_button)

        position_button = QPushButton("get position", clicked=self.get_position)
        hlayout.addWidget(position_button)

        self.lb_position = QLabel()
        hlayout.addWidget(self.lb_position)

        layout.addLayout(hlayout)

        # Setup the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_position)  # Connect the timeout signal to the function

    def load_video(self):
        """
        Load a video file in mpv.
        """

        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File")
        if not file_path:
            return
        self.mpv_widget.load_file(file_path)
        self.timer.start(200)

    def get_position(self):
        """
        get_position
        """
        self.lb_position.setText(str(self.mpv_widget.get_position()))

    def pause(self):
        self.mpv_widget.send_command({"command": ["set_property", "pause", True]})
        # self.timer.stop()

    def play(self):
        self.mpv_widget.send_command({"command": ["set_property", "pause", False]})
        # self.timer.start(200)

    def frame_forward(self):
        # self.mpv_widget.send_command({"command": ["show-text", "Frame forward", 5000]})
        self.mpv_widget.send_command({"command": ["frame-step"]})

    def frame_backward(self):
        self.mpv_widget.send_command({"command": ["frame-back-step"]})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
