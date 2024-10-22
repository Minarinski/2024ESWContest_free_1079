import sys
import time
from PyQt5.QtCore import QThread, QMutex
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

mutex = QMutex()  # 전역적으로 사용할 mutex

class WorkerThread(QThread):
    def __init__(self, label, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label

    def run(self):
        for i in range(5):
            # mutex 잠금
            mutex.lock()
            try:
                current_text = self.label.text()
                new_text = f"{current_text}\nThread {self.currentThreadId()} count: {i}"
                self.label.setText(new_text)
                # 시간이 걸리는 작업을 시뮬레이션
                time.sleep(1)
            finally:
                # 반드시 mutex를 해제해야 함
                mutex.unlock()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.label = QLabel("Starting threads...\n", self)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        # 스레드 생성
        self.thread1 = WorkerThread(self.label)
        self.thread2 = WorkerThread(self.label)

        # 스레드 시작
        self.thread1.start()
        self.thread2.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
