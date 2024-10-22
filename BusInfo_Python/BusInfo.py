# -*- coding: utf-8 -*-

import sys
import os
print(os.getcwd())
os.chdir('./BusInfo_Python')
print(os.getcwd())
import requests
import xmltodict
import time
import threading
import re
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QObject#, Qmutex
from PyQt5 import QtWidgets, QtCore, QtGui
import serial
from BusInfoPyQt import *
import pyttsx3

#mutex = QMutex()

flag = 0
GlobalArriveInfoList = []
GlobalBoardsList = []
speakList = []
speakBordingList = []

cntDownNum = 5
pageFix = False

class ApiThread(QThread):
    update_arrive_info = pyqtSignal(list)

    def __init__(self, key, BusStopID, BusStopArs):
        super().__init__()
        self.key = key
        self.BusStopID = BusStopID
        self.BusStopArs = BusStopArs
        

    def run(self):
        while self.key:
            response = requests.get(f'http://openapitraffic.daejeon.go.kr/api/rest/arrive/getArrInfoByStopID?serviceKey={self.key}&BusStopID={self.BusStopID}')
            ArriveInfoDict = xmltodict.parse(response.text)
            ArriveInfoListBefore = []
            #mutex.lock()
            try:
                for idx, ArriveInfo in enumerate(ArriveInfoDict['ServiceResult']['msgBody']['itemList']):
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
                    
                    global GlobalArriveInfoList
                    # 기존 isSpeaked 값을 유지하도록 수정
                    isSpeaked = 0
                    for idx, GlobalArriveInfo in enumerate(GlobalArriveInfoList):
                        if GlobalArriveInfo['ROUTE_NO'] == ArriveInfo['ROUTE_NO']:
                            isSpeaked = GlobalArriveInfoList[idx]['isSpeaked']
                            
                            break
                        else:
                            if GlobalArriveInfo['ROUTE_NO'][0]=='마':
                                if GlobalArriveInfo['ROUTE_NO'][-1] == ArriveInfo['ROUTE_NO']:
                                    isSpeaked = GlobalArriveInfoList[idx]['isSpeaked']
                                    
                                    break
                            isSpeaked = 0
                            

                    ArriveInfoListBefore.append([ArriveInfo['ROUTE_NO'], {
                        'ROUTE_NO': ArriveInfo['ROUTE_NO'],
                        'DESTINATION': ArriveInfo['DESTINATION'],
                        'EXTIME_MIN': ArriveInfo['EXTIME_MIN'],
                        'MSG_TP': ArriveInfo['MSG_TP'],
                        'BusStopNm': BusStopNm,
                        'CarNM': CarNM,
                        'RouteID': RouteID,
                        'isLowFloor': '0',
                        'isSpeaked': isSpeaked
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
                
                
                GlobalArriveInfoList = ArriveInfoList
            finally:
                pass

                #mutex.unlock()
            
            self.update_arrive_info.emit(ArriveInfoList)
            time.sleep(5)

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
        global flag, GlobalBoardsList, speakList, speakBordingList, GlobalArriveInfoList
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
                        if '2'+str(idx) not in GlobalBoardsList:
                            if '1'+str(idx) in GlobalBoardsList:
                                GlobalBoardsList.remove('1'+str(idx)) 
                            print(GlobalBoardsList, dataSplit[1]+str(idx)) 
                            GlobalBoardsList.append(dataSplit[1]+str(idx))
                            print(GlobalBoardsList)
                            n = GlobalArriveInfoList[idx]['ROUTE_NO']
                            if n != '999':
                                if dataSplit[1] == '1':
                                    speakBordingList.append(n+'번 버스 탑승을 요청하였습니다.')
                                else:
                                    speakBordingList.append(n+'번 버스 탑승 도움을 요청하였습니다.')
                            
                            print(idx, GlobalBoardsList)
                            txData = []
                            txData.append(str(dataSplit[1]))
                            if GlobalArriveInfoList[idx]['ROUTE_NO'][0] == '마':
                                txData.append(str('00' + GlobalArriveInfoList[idx]['ROUTE_NO'][-1]))
                            elif len(GlobalArriveInfoList[idx]['ROUTE_NO']) == 4:
                                txData.append("220")
                            else:
                                txData.append(str(GlobalArriveInfoList[idx]['ROUTE_NO'][:3]))
                            #txData.append(GlobalArriveInfoList[idx]['CarNM'][-4:])
                            txData.append('1315')
                            txData = ','.join(txData)
                            print(txData+'qwertyuiop')
                            txData2 = []
                            txData2.append('0000')
                            txData2.append(str(self.BusStopArs) + '@')
                            #txData2.append('23400' + '@')
                            txData2 = ''.join(txData2)
                            txData = (txData + '!' + txData2 + '!').encode('utf-8')                            
                            self.ser.write(stx + txData + etx)
                    else:
                        if '1'+str(idx) in GlobalBoardsList:
                            GlobalBoardsList.remove('1'+str(idx))
                        if '2'+str(idx) in GlobalBoardsList:
                            GlobalBoardsList.remove('2'+str(idx))
                        n = GlobalArriveInfoList[idx]['ROUTE_NO']
                        speakBordingList.append(n+'번 버스 탑승 요청을 취소하였습니다')
                        
                        txData = []
                        txData.append('0')
                        if GlobalArriveInfoList[idx]['ROUTE_NO'][0] == '마':
                            txData.append(str('00' + GlobalArriveInfoList[idx]['ROUTE_NO'][-1]))
                        elif len(GlobalArriveInfoList[idx]['ROUTE_NO']) == 4:
                            txData.append("220")
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
        global flag, pageFix
        while True:
            time.sleep(4)
            if self.pageCnt != 0 and pageFix == 0:
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
        chuns = ["", "천", "이천", "삼천"]
        # 문자열을 정수로 변환
        num = int(num_str)
        

        korean_number = ""

        # 천의 자리
        if num >= 1000:
            korean_number += chuns[num // 1000]
        
        # 백의 자리
        if num >= 100:
            korean_number += hundreds[num % 1000 // 100]
        
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
        elif text[3] == '번':
            self.engine.say(self.number_to_korean(text[:3]) + text[3:])
        else:
            self.engine.say(self.number_to_korean(text[:4]) + text[4:])
            
        self.engine.runAndWait()
    
    def run(self):
        global speakList, cntDownNum
        while True:
            if speakBordingList:
                self.speak(speakBordingList.pop(0))
                
            elif speakList:
                cntDownNum = 5
                for i in range(5):
                    time.sleep(1)
                    #print(f"cnt! : {cntDownNum}")
                    cntDownNum -= 1
                    #print(f"{cntDownNum}")
                self.speak(speakList.pop(0))
                

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
        self.backGroundImage = self.ui.label.setPixmap(QtGui.QPixmap("image/asset/background.png"))
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

        self.serial_thread = SerialThread('COM3', self.pageFlag, self.BusStopArs)
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
        self.timer.start(500)  # 1초마다 업데이트
        
        self.speakTimer = QTimer()
        self.speakTimer.timeout.connect(self.guideSound)
        self.speakTimer.start(240000)

    def setupUi(self):
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.showMaximized()
    
    def  keyPressEvent(self, e):
        if e.key() == 32:
            global pageFix
            if pageFix:
                pageFix = False
                self.ui.cnt_down.setStyleSheet("color: rgb(0, 0, 255);")
            else:
                pageFix = True
                self.ui.cnt_down.setStyleSheet("color: rgb(255, 0, 0);")
        elif e.key() == QtCore.Qt.Key_Escape:
            self.closeEvent()

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
        
        GlobalBoardsListLen = len(GlobalBoardsList)
        if GlobalBoardsListLen > 4:
            GlobalBoardsListLen = 4
        for i in range(GlobalBoardsListLen):
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
        global cntDownNum
        self.cnt = cntDownNum
        self.ui.label_23.setText(f"{self.now.month}월 {self.now.day}일")
        self.ui.label_24.setText(f"{self.now.hour:02d}:{self.now.minute:02d}")
        self.ui.cnt_down.setText(f"{self.cnt}")
        
        
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
        global GlobalBoardsList, GlobalArriveInfoList
        
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
            if GlobalArriveInfoList[idx]['ROUTE_NO'] not in self.nowArriveList:
                self.nowArriveList.append(GlobalArriveInfoList[idx]['ROUTE_NO'])
                self.nowArriveList.sort()
            self.labelList[i]['Minute'].setStyleSheet("color: rgb(255, 0, 4);")
            self.labelList[i]['Minute'].setText('진입중')
            #print(idx, self.BoardingNumList)
            if '1'+str(idx) in GlobalBoardsList:
                GlobalBoardsList.remove('1'+str(idx))
            if '2'+str(idx) in GlobalBoardsList:
                GlobalBoardsList.remove('2'+str(idx))
            #mutex.lock()
            try:
                if GlobalArriveInfoList[idx]['isSpeaked'] == 0:
                    GlobalArriveInfoList[idx]['isSpeaked'] = 1
                    speakList.append(GlobalArriveInfoList[idx]['ROUTE_NO']+'번 버스가 진입중입니다. 뒤로 한걸음 물러서 주세요')
            finally:
                pass
                #mutex.unlock()
                #self.serial_thread.update_boarding_info.emit(self.BoardingNumList)
                #self.updateBoardingInfo(self.serial_thread , self.BoardingNumList)
                #print(self.BoardingNumList)
        elif int(self.ArriveInfoList[idx]['EXTIME_MIN']) <= 3:
            self.labelList[i]['Minute'].setStyleSheet("color: rgb(255, 0, 4);")
            self.labelList[i]['Minute'].setText('잠시 후\n도착')
            if GlobalArriveInfoList[idx]['ROUTE_NO'] in self.nowArriveList:
                self.nowArriveList.remove(GlobalArriveInfoList[idx]['ROUTE_NO'])
                GlobalArriveInfoList[idx]['isSpeaked'] = 0
            
        else:
            if GlobalArriveInfoList[idx]['ROUTE_NO'] in self.nowArriveList:
                self.nowArriveList.remove(GlobalArriveInfoList[idx]['ROUTE_NO'])
                GlobalArriveInfoList[idx]['isSpeaked'] = 0
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
