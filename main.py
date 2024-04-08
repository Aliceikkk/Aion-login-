import os
import sys
import glob
import subprocess
import pickle
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont, QFontDatabase, QIcon
from PyQt5.QtCore import Qt, QTimer

class Launcher(QWidget):
    def __init__(self):
        super().__init__()

        
        self.setWindowTitle("永恒之塔启动器  by:nobody 交流群号：190635382")
        self.setGeometry(100, 100, 1024, 600)
        self.setFixedSize(1024, 600)  
        self.setStyleSheet("border-radius: 15px;")  

        
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = os.path.dirname(os.path.abspath(__file__))

        logo_file_path = os.path.join(bundle_dir, 'logo.ico')
        self.setWindowIcon(QIcon(logo_file_path))  

        background_images_path = os.path.join(bundle_dir, 'background_images/*.jpg')

        # Load background images
        self.background_images = glob.glob(background_images_path)
        self.current_image = 0
        self.background = QImage(self.background_images[self.current_image])

        # Load font
        font_db = QFontDatabase()
        font_file_path = os.path.join(bundle_dir, 'AaXinHuaMoZhuTi-2.ttf')
        font_id = font_db.addApplicationFont(font_file_path)
        if font_id != -1:
            self.font_family = font_db.applicationFontFamilies(font_id)[0]
        else:
            QMessageBox.critical(self, '错误', '字体加载失败')
            self.font_family = "Arial"

        # Add title image
        self.title_label = QLabel(self)
        self.title_label.setFont(QFont(self.font_family, 16))
        tit_file_path = os.path.join(bundle_dir, 'tit.png')
        pixmap = QPixmap(tit_file_path)
        self.title_label.setPixmap(pixmap.scaled(461, 170, Qt.KeepAspectRatio, Qt.FastTransformation))
        self.title_label.move(300, 20)

        # Add server IP label and line edit
        self.ip_label = QLabel("服务器地址:", self)
        self.ip_label.setFont(QFont(self.font_family, 16))
        self.ip_label.move(580, 400)
        self.ip_entry = QLineEdit(self)
        self.ip_entry.setFont(QFont(self.font_family, 16))
        self.ip_entry.setGeometry(700, 400, 200, 25)

        # Add game path label and line edit
        self.path_label = QLabel("游戏目录:", self)
        self.path_label.setFont(QFont(self.font_family, 16))
        self.path_label.move(600, 450)
        self.path_entry = QLineEdit(self)
        self.path_entry.setFont(QFont(self.font_family, 16))
        self.path_entry.setGeometry(700, 450, 200, 25)

        # Load user input
        if os.path.exists('user_input.pkl'):
            with open('user_input.pkl', 'rb') as f:
                ip, bin_path = pickle.load(f)
                self.ip_entry.setText(ip)
                self.path_entry.setText(bin_path)

        # Add start game button
        self.start_button = QPushButton('开始游戏', self)
        self.start_button.setFont(QFont(self.font_family, 16))
        self.start_button.setGeometry(700, 500, 80, 30)
        self.start_button.clicked.connect(self.start_aion)

        # Add select path button
        self.select_button = QPushButton('选择目录', self)
        self.select_button.setFont(QFont(self.font_family, 16))
        self.select_button.setGeometry(800, 500, 80, 30)
        self.select_button.clicked.connect(self.select_path)

        # Create a QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_background)
        self.timer.start(5000)  

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.background.scaled(self.size()))

    def start_aion(self):
        ip = self.ip_entry.text()
        bin_path = self.path_entry.text()

        if not ip:
            QMessageBox.warning(self, '警告', '请输入服务器地址！')
            return

        if not bin_path:
            QMessageBox.warning(self, '警告', '请选择游戏目录！')
            return

        # Save user input
        with open('user_input.pkl', 'wb') as f:
            pickle.dump((ip, bin_path), f)

        aion_bin_path = os.path.normpath(os.path.join(bin_path, "aion.bin"))
        if not os.path.exists(aion_bin_path):
            QMessageBox.warning(self, '警告', '无法在选择的目录中找到 aion.bin 文件！')
            return

        command = [aion_bin_path, "-ip:{}".format(ip), "-port:2106", "-cc:5", "-dist:93", "-lang:chs", "-megaphone", "-st", "-ingamebrowser", "-vip"]
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(command, shell=True, startupinfo=startupinfo)
        except Exception as e:
            QMessageBox.critical(self, '错误', f"启动游戏失败: {e}")

        # Minimize the window and hide it from the taskbar
        self.showMinimized()
        self.hide()

        # Start a QTimer to check if the game has exited every 5 seconds
        self.game_check_timer = QTimer()
        self.game_check_timer.timeout.connect(self.check_game_status)
        self.game_check_timer.start(5000)

    def select_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.path_entry.setText(path)

    def change_background(self):
        # Change background image
        self.current_image = (self.current_image + 1) % len(self.background_images)
        self.background = QImage(self.background_images[self.current_image])
        self.update()  # Trigger paintEvent

        # Show or hide title image
        if 'page1.jpg' in self.background_images[self.current_image]:
            self.title_label.show()
        else:
            self.title_label.hide()

    def check_game_status(self):
        # Check if the game is still running
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        game_process = subprocess.Popen(['tasklist'], stdout=subprocess.PIPE, text=True, startupinfo=startupinfo)
        output, _ = game_process.communicate()

        if 'aion.bin' not in output:
            # If the game has exited, show the window and stop the timer
            self.showNormal()
            self.game_check_timer.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec_())
