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
        self.connectionStatus = Label(text = "No client connected")
        
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
        if self.clientSocket != None:
            self.clientSocket.close()
        
        self.stopping = True
    
    #region Networking
    def openSocket(self):
        print("Starting server at: " + self.host + " on port: " + str(self.port))
        
        self.waitThread = threading.Thread(target = self.waitConnect)
        self.waitThread.start()
        
        print("Server started")
    
    def waitConnect(self):
        if self.s != None:
            self.s.close()
        
        if self.clientSocket != None:
            self.clientSocket.close()
        
        self.s = socket.socket()
        self.s.bind((self.host, self.port))
        
        print("Waiting for client to connect")
        
        self.s.listen(1)
        
        self.clientSocket, addr = self.s.accept()
        
        # Get connection info (client ip, port, client name)
        info = self.clientSocket.getpeername()
        clientName = socket.getfqdn(info[0])
        
        print("Connection from: " + str(info) + ", " + str(clientName))
        
        self.inputWidget.connected(str(info[0]), str(info[1]), str(clientName))
        
        print("Client is ready. Starting to send input data")
    
    def sendDataToClient(self, type, touch0, touch1, otherData):
        if (self.clientSocket == None or self.socketClosed()):
            self.openSocket()
            return
        
        data = self.compileDataIntoJson(type, touch0,touch1, otherData)

        jsobObj = json.dumps(data, indent = 4)
        
        self.clientSocket.send(jsobObj.encode('utf-8'))
    
    def socketClosed(self) -> bool:
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = self.clientSocket.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            logger.exception("unexpected exception when checking if a socket is closed")
            return False
        return False
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