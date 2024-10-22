import sys
import os
os.chdir('./BusDataLoader_Python')
import requests
import xmltodict
import json
from BusDataLoaderPyQt import *
import serial
import serial.tools.list_ports
import time
import datetime

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt  # Qt 임포트 추가
from PyQt5.QtGui import QFont  # QFont 임포트 추가
from PyQt5.QtGui import QIcon

ui = Ui_Dialog()

serial_connection = None

def getBusInfo(busname, busrouteno):
    f = open('key.txt', 'r')
    lines = f.readlines()
    d = {}
    for line in lines:
        a,b = line.split('=')
        d[a] = b if b[-1] != '\n' else b[:-1]
    key = d['key']
    BusRouteID = ''
    for idx in range(1,3):
        response = requests.get('http://openapitraffic.daejeon.go.kr/api/rest/busRouteInfo/getRouteInfoAll?serviceKey=Ya0Uj6qkt89wuBdfOjb1XMsBeY3iH8Rq8Mee9Luexx%2FNtfsc5%2F8eMZaNncY0Lo5lHFBKEayysnCd%2FKo4PxX5gg%3D%3D&reqPage='+str(idx))  
        dict_data = xmltodict.parse(response.text)

        for i in dict_data['ServiceResult']['msgBody']['itemList']:
            if i['ROUTE_NO'] == busrouteno:
                BusRouteID = i['ROUTE_CD']
                break
    print(BusRouteID)
    response = requests.get('http://openapitraffic.daejeon.go.kr/api/rest/busRouteInfo/getStaionByRoute?serviceKey='+key+'&busRouteId='+BusRouteID)    
    dict_data = xmltodict.parse(response.text)
    l = []
    for i in dict_data['ServiceResult']['msgBody']['itemList']:
        l.append({'busname': busname, 'busrouteno' : busrouteno, 'BusStopID':i['BUS_STOP_ID'], 'GPS_LATI':i['GPS_LATI'], 'GPS_LONG':i['GPS_LONG']})
    stx = 2
    stx = stx.to_bytes(1)
    etx = 3
    etx = etx.to_bytes(1)
    l = l[1:]
    
    dataJsonList = []
    
    for idx, i in enumerate(l):
        ui.progressBar.setValue(int((idx+1)*(100/len(l))))
        i['busrouteno'] = ('0'*(4-len(i['busrouteno'])))+i['busrouteno']
            
        f = ','.join([i['busname'], i['busrouteno'], i['BusStopID'][:5]])
        busStopName = dict_data['ServiceResult']['msgBody']['itemList'][idx]['BUSSTOP_NM']
        print(busStopName)
        tp = dict_data['ServiceResult']['msgBody']['itemList'][idx]['BUSSTOP_TP']
        if tp is None:
            tp = '0'
        f = 'D,' + tp + ',' +f
        f = f + ('0'*(20-len(f)))
        print('First = '+f, len(f))
        f = f.encode('utf-8')
        
        serial_connection.write(f)
        rx = serial_connection.readline().decode('utf-8')
        print(list(rx))
        # if 'N' not in rx:
        #     break
        
        s = ','.join([i['GPS_LATI'][:8], i['GPS_LONG'][:9]])
        s = 'd,'+s
        s = s + ('0'*(20-len(s)))
        print('Second = '+s, len(s))    
        s = s.encode('utf-8')
        
        serial_connection.write(s)
        rx = serial_connection.readline().decode('utf-8')
        print(list(rx))
        
        dataDict = {'busTP':tp, 'busName':i['busname'], 'busRouteNo':i['busrouteno'], 'busStopName':busStopName, 'BusStopID':i['BusStopID'][:5],'GPS_LATI':i['GPS_LATI'][:8], 'GPS_LONG':i['GPS_LONG'][:9]}
        dataJson = json.dumps(dataDict, ensure_ascii=False)
        dataJsonList.append(dataJson)
    stx = 2
    stx = stx.to_bytes(1)
    etx = 3
    etx = etx.to_bytes(1)
    data = ('OutPut'+('0'*14)).encode('utf-8')
    serial_connection.write(data)
    
    current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"{current_date}_{busrouteno}.txt", "w") as dataFile:
        print(os.getcwd())
        for data in dataJsonList:
            dataFile.write(f"{data}\n")
    
    msg_box()
            

def populate_ports():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        ui.PortCombo.addItem(port.device)

def populate_baudrates():
    baudrates = [115200, 9600, 248000]
    for baudrate in baudrates:
        ui.BaudrateCombo.addItem(str(baudrate))

def open_serial():
    global serial_connection
    port = ui.PortCombo.currentText()
    baudrate = ui.BaudrateCombo.currentText()
    if port and baudrate:
        try:
            serial_connection = serial.Serial(port, baudrate, timeout=1)
            ui.IsOpenLabel.setText("연결 완료")
            stx = 2
            stx = stx.to_bytes(1)
            etx = 3
            etx = etx.to_bytes(1)
            data = ('Input'+('0'*15)).encode('utf-8')
            serial_connection.write(data)
            
            ui.progressBar.setValue(0)
        except Exception as e:
            ui.IsOpenLabel.setText("연결 실패: {}".format(str(e)))

def close_serial():
    if serial_connection and serial_connection.is_open:
        serial_connection.close()
        ui.IsOpenLabel.setText("연결 끊김")

def print_bus_route():
    if serial_connection:
        bus_route_no = ui.BusRouteNoInput.text()
        bus_name = ui.BusNMInput.text()
        print("Bus Route No:", bus_route_no)
        print("Bus Name:", bus_name)
        getBusInfo(bus_name, bus_route_no)
    else:
        print('serial not open!!!!!!!')
        
def msg_box():
    dialog = QDialog()  # QDialog 생성
    dialog.setWindowTitle("다운로드 성공")  # 제목 설정
    dialog.setWindowFlag(Qt.FramelessWindowHint)  # 테두리 없는 창 설정 (필요시)

    dialog.setStyleSheet("QDialog { border: 2px solid black; border-radius: 5px; background-color: white; }") 

    layout = QVBoxLayout()  # 레이아웃 생성
    label = QLabel('<h2 style="text-align: center;">데이터 입력 완료</h2>')  # 중앙 정렬 텍스트
    font = QFont("NanumGothic", 12)  # 나눔고딕 폰트 설정 (크기 12)
    label.setFont(font)  # QLabel에 폰트 설정
    layout.addWidget(label)  # 레이아웃에 텍스트 추가

    button = QPushButton("확인")  # 확인 버튼
    button.clicked.connect(dialog.accept)  # 버튼 클릭 시 다이얼로그 닫기
    font = QFont("NanumGothic", 10)
    button.setFont(font)
    layout.addWidget(button)  # 레이아웃에 버튼 추가
    
    dialog.setLayout(layout)  # 다이얼로그 레이아웃 설정
    dialog.exec_()  # 다이얼로그 실행        



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    
    ui.setupUi(Dialog)
    Dialog.setWindowTitle("노선 데이터 입력")
    Dialog.setWindowIcon(QIcon('busIcon.png'))
    
    ui.OpenBtn.setFocus()
    
    Dialog.show()
    populate_ports()
    populate_baudrates()
    ui.OpenBtn.clicked.connect(open_serial)
    ui.CloseBtn.clicked.connect(close_serial)
    ui.BusRouteBtn.clicked.connect(print_bus_route)
    sys.exit(app.exec_())
