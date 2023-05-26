import os
#os.environ['KIVY_NO_CONSOLELOG'] = '1'

import socket
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from gestures4kivy import CommonGestures
import threading
import json
import logging

Config.set('input', 'mouse', 'mouse, multitouch_on_demand')
logger = logging.getLogger(__name__)

class InputWidget(Screen, CommonGestures):
    main = None
    
    dragging = False
    longPress = False
    
    DRAG_THRESHOLD = 2
    
    def __init__(self, main, hostIP, hostPort, **args):
        super().__init__(**args)
        
        self.main = main
        
        self.layout = BoxLayout(orientation = 'vertical')
        self.ipLabel = Label(text = "Host IP: " + hostIP + "     Host Port: " + hostPort)
        self.connectionStatus = Label(text = "Waiting for client to connect")
        
        self.layout.add_widget(self.ipLabel)
        self.layout.add_widget(self.connectionStatus)
        
        self.add_widget(self.layout)
    
    #region Input Methods
    def on_mouse_pos(self, instance, pos):
        # print("MouseHover")
        
        self.main.sendDataToClient("MouseHover", None, None, [("pos", pos)])
    
    def on_touch_down(self, touch):
        # print("ClickDown")
        
        if touch.button == 'middle':
            self.main.sendDataToClient("Click", touch, None, [])
        
        if touch.device == 'mouse':
            self.main.sendDataToClient("TouchDown", touch, None, [])
        
        super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # print("ClickUp")
        
        # self.main.sendDataToClient("ClickUp", touch, None, [])
        self.dragging = False
        
        super().on_touch_up(touch)
    
    def cgb_primary(self, touch, focus_x, focus_y):
        # print("ClickPrimary")
        
        self.main.sendDataToClient("Click", touch, None, [])
    
    def cgb_secondary(self, touch, focus_x, focus_y):
        # print("ClickSecondary")
        
        self.main.sendDataToClient("Click", touch, None, [])
        
    def cgb_select(self, touch, focus_x, focus_y, long_press):
        # print("TouchClick: " + str(long_press))
        
        self.dragging = False
        self.longPress = long_press
    
    def cgb_long_press_end(self, touch, focus_x, focus_y):
        # print("Long press" + (" DRAG" if self.dragging else "") +  " ended")
            
        self.main.sendDataToClient("LongPressUp", touch, None, [("fromDrag", self.dragging)])

        self.dragging = False
        self.longPress = False
    
    def cgb_drag(self, touch, focus_x, focus_y, delta_x, delta_y):
        if delta_x**2 + delta_y**2 < self.DRAG_THRESHOLD * self.DRAG_THRESHOLD:
            return
        
        self.dragging = True
        
        if self.longPress:
            self.longPress = False
            self.main.sendDataToClient("LongPressDown", touch, None, [])
        
        # print("Drag")
        
        self.main.sendDataToClient("Drag", touch, None, [("deltaX", delta_x), ("deltaY", delta_y)])
    
    def cgb_scroll(self, touch, focus_x, focus_y, delta_y, velocity):
        if not self.dragging:
            # print("Scroll")
            self.main.sendDataToClient("Scroll", touch, None, [("deltaY", delta_y), ("vel", velocity)])
    
    def cgb_pan(self, touch, focus_x, focus_y, delta_x, velocity):
        if not self.dragging:
            # print("Pan")
            self.main.sendDataToClient("Pan", touch, None, [("deltaX", delta_x), ("vel", velocity)])
    
    def cgb_zoom(self, touch0, touch1, focus_x, focus_y, delta_scale):
        if not self.dragging:
            # print("Zoom")
            self.main.sendDataToClient("Zoom", touch0, touch1, [("centerPos", (focus_x, focus_y)), ("deltaScale", delta_scale)])
    #endregion
    
    #region Info
    def connected(self, connectionIP, connectionPort, connectionName):
        self.updateStatusText("Connected to: " + connectionIP + ":" + connectionPort + " (" + connectionName + ")")
        
    def updateStatusText(self, newStatus):
        self.connectionStatus.text = newStatus
    
    def updateIPInfo(self, hostIP, hostPort):
        self.ipLabel.text = "Host IP: " + hostIP + "     Host Port: " + hostPort
    #endregion

class PenInputApp(App):
    clientSocket = None
    stopping = False
    
    s = None
    
    started = False
    
    waitThread = None
    
    # attemptNum = 1
    
    def build(self):
        self.sm = ScreenManager()
        
        self.host = str(socket.gethostbyname(socket.gethostname()))
        self.port = 9090
                
        self.inputWidget = InputWidget(main = self, hostIP = self.host, hostPort = str(self.port))
        Window.bind(mouse_pos = self.inputWidget.on_mouse_pos)
        
        self.sm.add_widget(self.inputWidget)
        
        self.openSocket()
        
        return self.sm
    
    def on_stop(self):
        self.closeSockets();
        
        self.stopping = True
        
        print("Stopping server")
        super().on_stop()
    
    #region Networking
    def openSocket(self):
        print("Starting server at: " + self.host + " on port: " + str(self.port))
        
        self.inputWidget.updateIPInfo(self.host, str(self.port))
        self.inputWidget.updateStatusText("Waiting for client to connect")
        
        self.closeSockets();
        
        if self.waitThread != None:
            self.waitThread.join()
        
        self.waitThread = threading.Thread(target = self.waitConnect)
        self.waitThread.start()
        
        print("Server started")
    
    def closeSockets(self):
        if self.s != None:
            self.s.close()
        
        if self.clientSocket != None:
            self.clientSocket.close()
        
        if self.waitThread != None:
            self.waitThread.join()
    
    def waitConnect(self):
        self.started = False
        
        self.closeSockets()
        
        self.s = socket.socket() #type = socket.SOCK_STREAM)
        self.s.bind((self.host, self.port))

        print("Waiting for client to connect")
        
        self.s.listen(1)
        
        # if self.socketClosed(self.s):
        #     print("Socket timed out. Retrying (attempt: " + str(self.attemptNum) + ")")
        #     self.attemptNum += 1
        #     self.waitConnect()
        #     return
        
        # self.attemptNum = 1
        
        self.clientSocket, addr = self.s.accept()
        
        self.clientSocket.settimeout(1)
        # self.clientSocket.setblocking(False)
        
        # Get connection info (client ip, port, client name)
        info = self.clientSocket.getpeername()
        clientName = socket.getfqdn(info[0])
        
        print("Connection from: " + str(info) + ", " + str(clientName))
        
        self.inputWidget.connected(str(info[0]), str(info[1]), str(clientName))
        
        self.started = True
        
        print("Client is ready. Starting to send input data")
    
    def sendDataToClient(self, type, touch0, touch1, otherData):
        try:
            data = self.compileDataIntoJson(type, touch0,touch1, otherData)

            jsobObj = json.dumps(data, indent = 4)
            
            self.clientSocket.send(jsobObj.encode('utf-8'))
        except:
            if not self.stopping and self.started:
                print("Client disconnected. Waiting for new client")
                self.waitConnect()
    
    def socketClosed(self, socket) -> bool:
        try:
            socket.send("IGNORE")
            return False
        except:
            return True
    #endregion
    
    #region Input Data
    def touchInfo(self, touch):
        if touch == None:
            return None
        
        infoDict = {
            "pos" : (touch.pos[0], touch.pos[1]),
            "button" : touch.button,
            "device" : touch.device,
            "shape" : (touch.shape.width, touch.shape.height) if touch.shape != None else None
        }
        
        return infoDict

    def compileDataIntoJson(self, type, touch0, touch1, otherData):
        dataDict = {}
        
        dataDict['type'] = type
        dataDict['touch0'] = self.touchInfo(touch0)
        dataDict['touch1'] = self.touchInfo(touch1)
        dataDict["screenSize"] = (self.sm.width, self.sm.height)
        
        for pair in otherData:
            dataDict[pair[0]] = pair[1]
        
        return dataDict
    #endregion

if __name__ == "__main__":
    PenInputApp().run()