import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class MyWindow(QMainWindow):
         
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test")
        self.setGeometry(1000, 200, 300, 300)

    def keyPressEvent(self, e): #키가 눌러졌을 때 실행됨
        if e.key() == Qt.Key_Escape:
            print("esc pressed")
        elif e.key() == Qt.Key_A:
            print("A is pressed)")
        else:
            print((e.key()))

    def keyReleaseEvent(self,e): #키를 누른상태에서 뗏을 때 실행됨
        print("kye is pressed:")
        print(e.key())
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()

    app.exec_()