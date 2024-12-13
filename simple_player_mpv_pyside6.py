"""
A simple Media Player using MPV and Pyside6


see https://mpv.io/manual/master/#command-interface

"""

import sys
import time
import mpv as mpv
from PySide6.QtGui import QCursor, QAction
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QApplication,
)


class Video_frame(QFrame):
    """
    QFrame class for visualizing video with VLC
    Frame emits a signal when clicked or resized
    """

    video_frame_signal = Signal(str, int)
    x_click, y_click = 0, 0

    '''
    # not working when video is playing!
    def mousePressEvent(self, QMouseEvent):
        """
        emits signal when mouse pressed on video
        """

        xm, ym = QMouseEvent.x(), QMouseEvent.y()
        button = QMouseEvent.button()
        print("video_frame", xm, ym)
    '''


class Player(QMainWindow):
    def __init__(self, master=None):
        QMainWindow.__init__(self, master)
        self.setWindowTitle("MPV - Media Player")

        self.createUI()
        self.isPaused = False

        self.lastPlayTime = 0
        self.lastPlayTimeGlobal = 0

    def my_log(self, loglevel, component, message):
        print("[{}] {}: {}".format(loglevel, component, message))

    def createUI(self):
        """Set up the user interface, signals & slots"""

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.videoframe = Video_frame(self)

        self.videoframe.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.videoframe.setAttribute(Qt.WA_NativeWindow)

        self.player = mpv.MPV(
            log_handler=self.my_log,
            wid=str(int(self.videoframe.winId())),
            # player_operation_mode='pseudo-gui',
            # vo='x11', # You may not need this
            # log_handler=print,
            loglevel="info",
        )

        @self.player.on_key_press("MBTN_LEFT")
        def mbtn_left():
            print()
            print("MBTN_LEFT")
            print(f"{self.player.mouse_pos=}")

            print(f"{self.player.width=}")
            print(f"{self.player.height=}")
            # print(f"{self.videoframe.size().width()=}")
            print(f"{self.videoframe.size().width()/ self.videoframe.size().height()=}")

            print(f"{self.player.width / self.player.height=}")

            vw = self.player.width
            vh = self.player.height

            fw = self.videoframe.size().width()
            fh = self.videoframe.size().height()

            if fw / fh >= self.player.width / self.player.height:  # vertical black lane
                x = vw / vh * fh
                offset = (fw - x) / 2
                px = self.player.mouse_pos["x"] - offset
                if 0 <= px < x:
                    px = round((px / x) * self.player.width)
                else:
                    px = "out"
                py = round(self.player.mouse_pos["y"] / self.videoframe.size().height() * self.player.height)

            else:
                y = fw / vw * vh
                offset = (fh - y) / 2
                py = self.player.mouse_pos["y"] - offset
                if 0 <= py < y:
                    py = round((py / y) * self.player.height)
                else:
                    py = "out"
                px = round(self.player.mouse_pos["x"] / self.videoframe.size().width() * self.player.width)

            print(f"{px=}  {py=}")

            print(f"{px / self.player.width=}")

            self.player.video_pan_x = -(px / self.player.width) + 0.5
            self.player.video_pan_y = -(py / self.player.height) + 0.5

            self.player.video_zoom = 1

        @self.player.on_key_press("MBTN_RIGHT")
        def mbtn_right():
            self.player.video_pan_x = 0
            self.player.video_pan_y = 0

            self.player.video_zoom = 0

        @self.player.on_key_press("MBTN_LEFT_DBL")
        def mbtn_dbl_left():
            print("MBTN_LEFT_DBL")
            print(self.player.mouse_pos)

        @self.player.property_observer("time-pos")
        def time_observer(_name, value):
            if value is not None:
                self.label.setText(f"{value:.3f} frame: {round(value * 25) + 1}")
                self.positionslider.setValue(int(value / self.player.duration * 1000))

        self.positionslider = QSlider(Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.setPosition)

        self.hbuttonbox = QHBoxLayout()

        self.label = QLabel()
        self.hbuttonbox.addWidget(self.label)

        self.playbutton = QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        self.playbutton.clicked.connect(self.PlayPause)

        self.stopbutton = QPushButton("Stop")
        self.hbuttonbox.addWidget(self.stopbutton)
        self.stopbutton.clicked.connect(self.Stop)

        self.infobutton = QPushButton("info")
        self.hbuttonbox.addWidget(self.infobutton)
        self.infobutton.clicked.connect(self.info)

        self.frame = QPushButton("frame +")
        self.hbuttonbox.addWidget(self.frame)
        self.frame.clicked.connect(self.frame_clicked)

        self.frame_back = QPushButton("frame -")
        self.hbuttonbox.addWidget(self.frame_back)
        self.frame_back.clicked.connect(self.frame_back_clicked)

        self.slow = QPushButton("slower", clicked=self.slow_clicked)
        self.hbuttonbox.addWidget(self.slow)

        self.fast = QPushButton("faster", clicked=self.fast_clicked)
        self.hbuttonbox.addWidget(self.fast)

        self.extract_frame = QPushButton("Extract frame", clicked=self.extract_frame)
        self.hbuttonbox.addWidget(self.extract_frame)

        self.test_button = QPushButton("Test", clicked=self.test_button)
        self.hbuttonbox.addWidget(self.test_button)

        self.hbuttonbox.addStretch(1)
        self.volumeslider = QSlider(Qt.Horizontal, self)
        self.volumeslider.setMaximum(100)
        self.volumeslider.setToolTip("Volume")
        self.hbuttonbox.addWidget(self.volumeslider)
        self.volumeslider.valueChanged.connect(self.setVolume)

        self.vboxlayout = QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)

        self.frame_label = QLabel("LABEL")
        self.vboxlayout.addWidget(self.frame_label)

        self.vboxlayout.addWidget(self.positionslider)

        self.vboxlayout.addLayout(self.hbuttonbox)

        self.widget.setLayout(self.vboxlayout)

        open = QAction("&Open", self)
        open.triggered.connect(self.OpenFile)
        exit = QAction("&Exit", self)
        exit.triggered.connect(sys.exit)

        menubar = self.menuBar()
        filemenu = menubar.addMenu("&File")
        filemenu.addAction(open)
        filemenu.addSeparator()
        filemenu.addAction(exit)

    def test_button(self):
        """
        test_button clicked
        """
        print("test")

    def extract_frame(self):
        """
        extract frame from video and visualize it in frame_viewer

        see https://mpv.io/manual/master/#command-interface-screenshot-raw

        """

        """
        image_qt = ImageQt(self.player.screenshot_raw())
        pixmap = QPixmap.fromImage(image_qt)

        self.frame_label.setPixmap(pixmap.scaled(self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        """

    """
    def mousePressEvent(self, event):
        print(f"QMainwindow event: {event}")
    """

    def keyPressEvent(self, event):
        print()

        print("main window", self.geometry())

        print("self.videoframe.geometry()", self.videoframe.geometry())
        cursor = QCursor()
        print("cursor pos:", cursor.pos())

        print(
            cursor.pos().x() - (self.geometry().x() + self.videoframe.geometry().x()),
            cursor.pos().y() - (self.geometry().y() + self.videoframe.geometry().y()),
        )

    def frame_clicked(self):
        self.player.command("frame-step")

    def frame_back_clicked(self):
        self.player.command("frame-back-step")

    def setVolume(self):
        print("not implemented yet")

    def slow_clicked(self):
        print("speed before", self.player.speed)
        if self.player.speed > 0.1:
            self.player.speed = round(self.player.speed - 0.1, 3)
        print("speed after", self.player.speed)

    def fast_clicked(self):
        print("speed before", self.player.speed)
        self.player.speed = round(self.player.speed + 0.1, 3)
        print("speed after", self.player.speed)

    def PlayPause(self):
        """
        Toggle play/pause status
        """

        if not self.player.filename:
            if len(sys.argv) == 1:
                self.OpenFile()
            else:
                self.OpenFile(sys.argv[1])

        self.player.pause = not self.player.pause

        self.info()

    def info(self):
        print("==================================")
        """
        print(f"file name: {self.player.filename}")
        print(f"file path: {self.player.path}")
        print(f"file format: {self.player.file_format}")
        """

        print(f"status_term_msg: {self.player.term_status_msg}")
        print(f"pause: {self.player.pause}")
        print(f"end: {self.player.end}")
        print(f"endpos: {self.player.endpos}")
        print(f"time_pos: {self.player.time_pos}")
        print("self.player.playback_time", self.player.playback_time)
        print(f"duration: {self.player.duration}")
        print(f"frames: {self.player.estimated_frame_number}/{self.player.estimated_frame_count}")
        print(f"video_speed_correction: {self.player.video_speed_correction}")
        # self.player.video_speed_correction = self.player.video_speed_correction * 1.1
        print(f"FPS: {self.player.container_fps}")

        print(f"dim: {self.player.width} x {self.player.height}")

        print(f"video frame size: {self.videoframe.size()} {self.videoframe.size().width()/self.videoframe.size().height()}")

        print("self.player.playlist_pos", self.player.playlist_pos)
        print("self.player.playlist", self.player.playlist)
        if self.player.playlist_pos:
            print("self.player.playlist", self.player.playlist[self.player.playlist_pos])

    def Stop(self):
        """
        Stop player
        """
        self.player.command("stop")
        print("player stopped")

        self.info()

    def OpenFile(self, filename=None):
        """
        Open a media file in a MediaPlayer
        """

        if not filename:
            filename, _ = QFileDialog.getOpenFileName(self, "Open File", "")
        if not filename:
            return

        self.player.playlist_append(filename)
        # self.player.playlist_append(filename2)
        self.player.playlist_pos = 0
        print("self.player.playlist1", self.player.playlist)

        self.player.keep_open = True

        self.player.pause = False
        print("player play")

        self.player.wait_until_playing()
        print("wait until playing")

        self.player.pause = True
        # self.player.wait_until_paused()
        self.player.seek(0, "absolute")

        self.info()

    def setPosition(self, position):
        """
        Set position of video in base of slider position
        """
        new_pos = self.player.duration * (position / 1000.0)
        print("new_pos", new_pos)
        self.player.command("seek", str(new_pos), "absolute")

    def resizeEvent(self, event):
        print("resize", event)
        try:
            self.overlay.remove()
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    import locale

    locale.setlocale(locale.LC_NUMERIC, "C")

    player = Player()
    player.show()
    player.resize(640, 480)
    if sys.argv[1:]:
        player.OpenFile(sys.argv[1])
    sys.exit(app.exec_())
