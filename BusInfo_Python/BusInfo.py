# -*- coding: utf-8 -*-

import sys
import os
print(os.getcwd())
os.chdir('C:/Users/DSM2022/Documents/2024ESWContest_free_1079/BusInfo_Python')
print(os.getcwd())
import requests
import xmltodict
import time
import threading
import re
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QObject
from PyQt5 import QtWidgets, QtCore, QtGui
import serial
from BusInfoPyQt import *
import pyttsx3

flag = 0
GlobalArriveInfoList = []
GlobalBoardsList = []
speakList = []

class ApiThread(QThread):
    update_arrive_info = pyqtSignal(list)

    def __init__(self, key, BusStopID, BusStopArs):
        super().__init__()
        self.key = key
        self.BusStopID = BusStopID
        self.BusStopArs = BusStopArs
        

    def run(self):
        while True:
            response = requests.get(f'http://openapitraffic.daejeon.go.kr/api/rest/arrive/getArrInfoByStopID?serviceKey={self.key}&BusStopID={self.BusStopID}')
            ArriveInfoDict = xmltodict.parse(response.text)
            ArriveInfoListBefore = []
            for ArriveInfo in ArriveInfoDict['ServiceResult']['msgBody']['itemList']:
                BusStopNm = '운행대기'
                RouteID = ''
                CarNM = ''

                if ArriveInfo['MSG_TP'] != '07' and ArriveInfo['MSG_TP'] != '06':
                    if len(ArriveInfo) != 2:
                        #print(ArriveInfo, len(ArriveInfo))
                        if 'LAST_STOP_ID' in ArriveInfo.keys():
                            arsId = ArriveInfo['LAST_STOP_ID']
                    elif len(ArriveInfo) == 2:
                        print(ArriveInfo, len(ArriveInfo))
                        if 'LAST_STOP_ID' in ArriveInfo[0].keys():
                            arsId = ArriveInfo[0]['LAST_STOP_ID']
                    else:
                        arsId = None
                    if len(ArriveInfo) != 0  and arsId:
                        response = requests.get(f'http://openapitraffic.daejeon.go.kr/api/rest/stationinfo/getStationByUid?serviceKey={self.key}&arsId={arsId}')
                        BusStopDict = xmltodict.parse(response.text)
                        if isinstance(BusStopDict['ServiceResult']['msgBody']['itemList'], dict):
                            if 'BUSSTOP_NM' in BusStopDict['ServiceResult']['msgBody']['itemList'].keys():
                                BusStopNm = BusStopDict['ServiceResult']['msgBody']['itemList']['BUSSTOP_NM']
                        else:
                            if 'BUSSTOP_NM' in BusStopDict['ServiceResult']['msgBody']['itemList'][0].keys():
                                BusStopNm = BusStopDict['ServiceResult']['msgBody']['itemList'][0]['BUSSTOP_NM']
                    RouteID = ArriveInfo['ROUTE_CD']
                    CarNM = ArriveInfo['CAR_REG_NO']
                    
                    
                ArriveInfoListBefore.append([ArriveInfo['ROUTE_NO'], {
                    'ROUTE_NO': ArriveInfo['ROUTE_NO'],
                    'DESTINATION': ArriveInfo['DESTINATION'],
                    'EXTIME_MIN': ArriveInfo['EXTIME_MIN'],
                    'MSG_TP': ArriveInfo['MSG_TP'],
                    'BusStopNm': BusStopNm,
                    'CarNM': CarNM,
                    'RouteID': RouteID,
                    'isLowFloor': '0'
                }])
            ArriveInfoListBefore.sort()
            ArriveInfoList = [item[1] for item in ArriveInfoListBefore]

            for i in range(len(ArriveInfoList)):
                if len(ArriveInfoList[i]['ROUTE_NO']) == 1:
                    ArriveInfoList[i]['ROUTE_NO'] = '마을'+ArriveInfoList[i]['ROUTE_NO']
            
            while len(ArriveInfoList) % 5 != 0:
                ArriveInfoList.append({
                    'ROUTE_NO': '999', 'DESTINATION': '', 'EXTIME_MIN': '',
                    'MSG_TP': '', 'BusStopNm': '', 'CarNM': '', 'RouteID': '', 'isLowFloor': '0'
                })
            
            global GlobalArriveInfoList
            GlobalArriveInfoList = ArriveInfoList
            
            self.update_arrive_info.emit(ArriveInfoList)
            time.sleep(2)

class SerialThread(QThread):
    update_boarding_info = pyqtSignal(list)

    def __init__(self, serial_port, pageFlag, BusStopArs):
        super().__init__()
        try:
            self.ser = serial.Serial(
                port=serial_port, 
                baudrate=115200, 
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=8
            )
        except:
            print('Serial port open error')
            self.ser = None
        self.pageFlag = pageFlag
        self.BoardingNumList = []
        self.BusStopArs = BusStopArs
         

    def run(self):
        pattern = re.compile('^0x02.*0x03$')
        global flag, GlobalBoardsList, speakList, GlobalArriveInfoList
        stx = 2
        stx = stx.to_bytes(1)
        etx = 3
        etx = etx.to_bytes(1)
        while self.ser:
            if self.ser.in_waiting > 0:
                data = self.ser.readline().decode('utf-8').rstrip()
                print(data)
                if pattern.match(data):
                    dataSplit = data[4:-4].split(',')
                    idx = int(dataSplit[0]) + (5 * flag)
                    if dataSplit[1] == '1' or dataSplit[1] == '2':
                        if '2'+str(idx) not in GlobalBoardsList and idx < 6:
                            if '1'+str(idx) in GlobalBoardsList:
                                GlobalBoardsList.remove('1'+str(idx)) 
                            print(GlobalBoardsList, dataSplit[1]+str(idx)) 
                            GlobalBoardsList.append(dataSplit[1]+str(idx))
                            print(GlobalBoardsList)
                            n = GlobalArriveInfoList[idx]['ROUTE_NO']
                            if dataSplit[1] == '1':
                                speakList.append(n+'번 버스 호출 완료')
                            else:
                                speakList.append(n+'번 버스 호출 완료. 탑승 도움을 요청했습니다.')
                            
                            print(idx, GlobalBoardsList)
                            txData = []
                            txData.append(str(dataSplit[1]))
                            if GlobalArriveInfoList[idx]['ROUTE_NO'][0] == '마':
                                txData.append(str('00' + GlobalArriveInfoList[idx]['ROUTE_NO'][-1]))
                            else:
                                txData.append(str(GlobalArriveInfoList[idx]['ROUTE_NO']))
                            #txData.append(GlobalArriveInfoList[idx]['CarNM'][-4:])
                            txData.append('1315')
                            txData = ','.join(txData)
                            txData2 = []
                            txData2.append('0000')
                            txData2.append(str(self.BusStopArs) + '@')
                            txData2 = ''.join(txData2)
                            txData = (txData + '!' + txData2 + '!').encode('utf-8')                            
                            self.ser.write(stx + txData + etx)
                    else:
                        if '1'+str(idx) in GlobalBoardsList:
                            GlobalBoardsList.remove('1'+str(idx))
                        if '2'+str(idx) in GlobalBoardsList:
                            GlobalBoardsList.remove('2'+str(idx))
                        n = GlobalArriveInfoList[idx]['ROUTE_NO']
                        speakList.append(n+'번 버스 호출이 취소되었습니다')
                        
                        txData = []
                        txData.append('0')
                        if GlobalArriveInfoList[idx]['ROUTE_NO'][0] == '마':
                            txData.append(str('00' + GlobalArriveInfoList[idx]['ROUTE_NO'][-1]))
                        else:
                            txData.append(str(GlobalArriveInfoList[idx]['ROUTE_NO']))
                        #txData.append(GlobalArriveInfoList[idx]['CarNM'][-4:])
                        txData.append('1315')
                        txData = ','.join(txData)
                        txData2 = []
                        txData2.append('0000')
                        txData2.append(str(self.BusStopArs) + '@')
                        txData2 = ''.join(txData2)
                        txData = (txData + '!' + txData2 + '!').encode('utf-8')                            
                        self.ser.write(stx + txData + etx)
                        
                            
            self.update_boarding_info.emit(self.BoardingNumList)

class PageFlagThread(QThread):
    update_page_flag = pyqtSignal(int)

    def __init__(self, pageCnt):
        super().__init__()
        self.pageCnt = pageCnt
        self.pageFlag = 0

    def run(self):
        global flag
        while True:
            time.sleep(7)
            if self.pageCnt != 0:
                self.pageFlag = (self.pageFlag + 1) % self.pageCnt
            self.update_page_flag.emit(self.pageFlag)
            flag = self.pageFlag

class SpeakThread(QThread):
    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        
    def number_to_korean(self, num_str):
        # 한국어 숫자 표현
        units = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
        tens = ["", "십", "이십", "삼십", "사십", "오십", "육십", "칠십", "팔십", "구십"]
        hundreds = ["", "백", "이백", "삼백", "사백", "오백", "육백", "칠백", "팔백", "구백"]

        # 문자열을 정수로 변환
        num = int(num_str)
        
        if num < 1 or num > 1000:
            return "범위를 벗어난 숫자입니다. (1-1000)"

        if num == 1000:
            return "천"

        korean_number = ""

        # 백의 자리
        if num >= 100:
            korean_number += hundreds[num // 100]
        
        # 십의 자리
        if num >= 10:
            korean_number += tens[(num % 100) // 10]
        
        # 일의 자리
        korean_number += units[num % 10]

        return korean_number.strip()

    def speak(self, text):
        if text[0] == '몸':
            self.engine.say(text)
        elif text[0] == '마':
            self.engine.say(text[:2] + self.number_to_korean(text[2]) + text[3:])
        else:
            self.engine.say(self.number_to_korean(text[:3]) + text[3:])
        self.engine.runAndWait()
    
    def run(self):
        global speakList
        while True:
            if speakList:
                self.speak(speakList.pop(0))
                time.sleep(3)

class BusArrivalApp(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi()
        
        self.now = datetime.now()
        
        self.key = ''
        self.BusStopID = ''
        self.BusStopArs = ''
        self.ArriveInfoList = []
        self.pageFlag = 0
        self.BoardingNumList = []
        self.ADImageList = [
            'image/AD/1.png', 'image/AD/2.png', 'image/AD/3.png',
            'image/AD/4.png', 'image/AD/5.png'
        ]
        
        self.labelList = [{'Route': self.ui.label_2, 'Destination': self.ui.label_3, 'Minute': self.ui.label_4, 'Location': self.ui.label_5, 'Icon': self.ui.label_25},
                    {'Route': self.ui.label_6, 'Destination': self.ui.label_7, 'Minute': self.ui.label_8, 'Location': self.ui.label_9, 'Icon': self.ui.label_26},
                    {'Route': self.ui.label_10, 'Destination': self.ui.label_11, 'Minute': self.ui.label_12, 'Location': self.ui.label_13, 'Icon': self.ui.label_27},
                    {'Route': self.ui.label_14, 'Destination': self.ui.label_15, 'Minute': self.ui.label_16, 'Location': self.ui.label_17, 'Icon': self.ui.label_28},
                    {'Route': self.ui.label_18, 'Destination': self.ui.label_19, 'Minute': self.ui.label_20, 'Location': self.ui.label_21, 'Icon': self.ui.label_29}]
        self.BoardingUiList = [self.ui.label_32, self.ui.label_33, self.ui.label_34, self.ui.label_35]
        
        
        self.nowArriveList = []
        
        self.getKey("key.txt")
        self.getInfo("./info.txt")

        # QThreads
        self.api_thread = ApiThread(self.key, self.BusStopID, self.BusStopArs)
        self.api_thread.update_arrive_info.connect(self.updateArriveInfo)
        self.api_thread.start()

        self.serial_thread = SerialThread('COM8', self.pageFlag, self.BusStopArs)
        self.serial_thread.update_boarding_info.connect(self.updateBoardingInfo)
        self.serial_thread.start()

        self.page_flag_thread = PageFlagThread(len(self.ArriveInfoList)//5)
        self.page_flag_thread.update_page_flag.connect(self.updatePageFlag)
        self.page_flag_thread.start()
        
        self.speak_thread = SpeakThread()
        self.speak_thread.start()

        self.updateAdsCnt = 0

        # GUI 업데이트를 위한 타이머
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGui)
        self.timer.start(1000)  # 1초마다 업데이트
        
        self.speakTimer = QTimer()
        self.speakTimer.timeout.connect(self.guideSound)
        self.speakTimer.start(40000)

    def setupUi(self):
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.showMaximized()

    def getInfo(self, filename):
        print(filename)
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                d = {}
                for line in lines:
                    a, b = line.split('=')
                    d[a] = b.strip()
                self.BusStopID = d['BusStopID']
                self.BusStopArs = d['BusStopArs']
        except:
            print("info.txt file not found.")
            
    def getKey(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                d = {}
                for line in lines:
                    a, b = line.split('=')
                    d[a] = b.strip()
                self.key = d['key']
        except:
            print("key.txt file not found.")

    def updateArriveInfo(self, ArriveInfoList):
        self.ArriveInfoList = ArriveInfoList
        self.page_flag_thread.pageCnt = len(self.ArriveInfoList)//5

    def updateBoardingInfo(self, BoardingNumList):
        global GlobalBoardsList
        self.BoardingNumList = BoardingNumList
        GlobalBoardsList.sort()
        #print(self.BoardingNumList)
        
        for i in range(4):
            self.BoardingUiList[i].setText('')
        
        for i in range(len(GlobalBoardsList)):
            if self.ArriveInfoList[int(GlobalBoardsList[i][1:])]['ROUTE_NO'] != '999':
                if GlobalBoardsList[i][0] == '1':
                    self.BoardingUiList[i].setStyleSheet("color: rgb(255, 0, 0);")
                    self.BoardingUiList[i].setText(self.ArriveInfoList[int(GlobalBoardsList[i][1:])]['ROUTE_NO'])
                else:
                    self.BoardingUiList[i].setStyleSheet("color: rgb(0, 255, 0);")
                    self.BoardingUiList[i].setText(self.ArriveInfoList[int(GlobalBoardsList[i][1:])]['ROUTE_NO'])
            else:
                self.BoardingUiList[i].setText('')  

    def updatePageFlag(self, pageFlag):
        self.pageFlag = pageFlag
        
    def guideSound(self):
        global speakList
        speakList.append('몸이 불편하신 분은, 버튼을 2초간 누르시면, 기사님께 탑승도움을 요청 할 수 있습니다.')

    def updateGui(self):
        self.now = datetime.now()
        self.ui.label_23.setText(f"{self.now.month}월 {self.now.day}일")
        self.ui.label_24.setText(f"{self.now.hour:02d}:{self.now.minute:02d}")
        
        for i in range(5):
            idx = i + (5 * self.pageFlag)
            if self.ArriveInfoList:
                if self.ArriveInfoList[idx]['ROUTE_NO'] == '999':
                    self.clearRouteInfo(i)
                else:
                    self.updateRouteInfo(i, idx)
        
        self.updateAds()
        self.updateNowArrive()

    def clearRouteInfo(self, i):
        self.labelList[i]['Route'].setText('')
        self.labelList[i]['Destination'].setText('')
        self.labelList[i]['Minute'].setText('')
        self.labelList[i]['Location'].setText('')

    def updateRouteInfo(self, i, idx):
        global GlobalBoardsList
        
        if self.ArriveInfoList[idx]['ROUTE_NO'][:2] == '마을' or len(self.ArriveInfoList[idx]['ROUTE_NO']) == 1:
            self.labelList[i]['Icon'].setPixmap(QtGui.QPixmap("image/asset/maeul.png"))
        else:
            self.labelList[i]['Icon'].setPixmap(QtGui.QPixmap("image/asset/not.png"))
        self.labelList[i]['Icon'].setScaledContents(True)
        self.labelList[i]['Route'].setText(self.ArriveInfoList[idx]['ROUTE_NO'])
        self.labelList[i]['Destination'].setText(self.ArriveInfoList[idx]['DESTINATION'])
        self.labelList[i]['Location'].setText(self.ArriveInfoList[idx]['BusStopNm'])
        if self.ArriveInfoList[idx]['MSG_TP'] == '07':
            self.labelList[i]['Minute'].setStyleSheet("color: rgb(255, 255, 255);")
            self.labelList[i]['Minute'].setText('운행대기')
            if GlobalArriveInfoList[idx]['ROUTE_NO'] in self.nowArriveList:
                self.nowArriveList.remove(GlobalArriveInfoList[idx]['ROUTE_NO'])
        elif self.ArriveInfoList[idx]['MSG_TP'] == '06':
            if not self.nowArriveList:
                self.nowArriveList.append(GlobalArriveInfoList[idx]['ROUTE_NO'])
            self.labelList[i]['Minute'].setStyleSheet("color: rgb(255, 0, 4);")
            self.labelList[i]['Minute'].setText('진입중')
            #print(idx, self.BoardingNumList)
            if '1'+str(idx) in GlobalBoardsList:
                GlobalBoardsList.remove('1'+str(idx))
            if '2'+str(idx) in GlobalBoardsList:
                GlobalBoardsList.remove('2'+str(idx))
            if GlobalArriveInfoList[idx]['ROUTE_NO']+'번 버스가 진입중입니다. 뒤로 한걸음 물러서 주세요' not in speakList:
                speakList.append(GlobalArriveInfoList[idx]['ROUTE_NO']+'번 버스가 진입중입니다. 뒤로 한걸음 물러서 주세요')
                #self.serial_thread.update_boarding_info.emit(self.BoardingNumList)
                #self.updateBoardingInfo(self.serial_thread , self.BoardingNumList)
                #print(self.BoardingNumList)
        elif int(self.ArriveInfoList[idx]['EXTIME_MIN']) <= 3:
            self.labelList[i]['Minute'].setStyleSheet("color: rgb(255, 0, 4);")
            self.labelList[i]['Minute'].setText('잠시 후\n도착')
        else:
            if GlobalArriveInfoList[idx]['ROUTE_NO'] in self.nowArriveList:
                self.nowArriveList.remove(GlobalArriveInfoList[idx]['ROUTE_NO'])
            self.labelList[i]['Minute'].setStyleSheet("color: rgb(255, 255, 255);")
            self.labelList[i]['Minute'].setText(self.ArriveInfoList[idx]['EXTIME_MIN'] + '분')

    def updateAds(self):
        if self.updateAdsCnt == 0:
            self.ui.label_30.setPixmap(QtGui.QPixmap(self.ADImageList[0]))
            self.ui.label_30.setScaledContents(True)
            self.ui.label_31.setPixmap(QtGui.QPixmap(self.ADImageList[1]))
            self.ui.label_31.setScaledContents(True)
            self.ADImageList.append(self.ADImageList.pop(0))
        self.updateAdsCnt = (self.updateAdsCnt + 1) % 7

    def updateNowArrive(self):
        self.nowArriveStr = ' '.join(self.nowArriveList)
        self.ui.label_22.setText(self.nowArriveStr)

    def closeEvent(self, event):
        # 창을 닫을 때 모든 스레드를 안전하게 종료
        self.api_thread.quit()
        self.api_thread.wait()
        
        self.serial_thread.quit()
        self.serial_thread.wait()
        
        self.page_flag_thread.quit()
        self.page_flag_thread.wait()
        
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = BusArrivalApp()
    sys.exit(app.exec_())
