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

Config.set('input', 'mouse', 'mouse, multitouch_on_demand')

class InputWidget(Screen, CommonGestures):
    clientSocket = None
    
    dragging = False
    longPress = False
    
    DRAG_THRESHOLD = 2
    
    def __init__(self, hostIP, hostPort, **args):
        super().__init__(**args)
        
        self.label = Label(text = "Host IP: " + hostIP + "     Host Port: " + hostPort)
        
        self.add_widget(self.label)
    
    #region Input Methods
    def on_mouse_pos(self, instance, pos):
        # print("MouseHover")
        
        self.sendDataToClient("MouseHover", None, None, [("pos", pos)])
    
    def on_touch_down(self, touch):
        # print("ClickDown")
        
        if touch.button == 'middle':
            self.sendDataToClient("Click", touch, None, [])
        
        if touch.device == 'mouse':
            self.sendDataToClient("TouchDown", touch, None, [])
        
        super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # print("ClickUp")
        
        # self.sendDataToClient("ClickUp", touch, None, [])
        self.dragging = False
        
        super().on_touch_up(touch)
    
    def cgb_primary(self, touch, focus_x, focus_y):
        # print("ClickPrimary")
        
        self.sendDataToClient("Click", touch, None, [])
    
    def cgb_secondary(self, touch, focus_x, focus_y):
        # print("ClickSecondary")
        
        self.sendDataToClient("Click", touch, None, [])
        
    def cgb_select(self, touch, focus_x, focus_y, long_press):
        # print("TouchClick: " + str(long_press))
        
        self.dragging = False
        self.longPress = long_press
    
    def cgb_long_press_end(self, touch, focus_x, focus_y):
        # print("Long press" + (" DRAG" if self.dragging else "") +  " ended")
            
        self.sendDataToClient("LongPressUp", touch, None, [("fromDrag", self.dragging)])

        self.dragging = False
        self.longPress = False
    
    def cgb_drag(self, touch, focus_x, focus_y, delta_x, delta_y):
        if delta_x**2 + delta_y**2 < self.DRAG_THRESHOLD * self.DRAG_THRESHOLD:
            return
        
        self.dragging = True
        
        if self.longPress:
            self.longPress = False
            self.sendDataToClient("LongPressDown", touch, None, [])
        
        # print("Drag")
        
        self.sendDataToClient("Drag", touch, None, [("deltaX", delta_x), ("deltaY", delta_y)])
    
    def cgb_scroll(self, touch, focus_x, focus_y, delta_y, velocity):
        if not self.dragging:
            # print("Scroll")
            self.sendDataToClient("Scroll", touch, None, [("deltaY", delta_y), ("vel", velocity)])
    
    def cgb_pan(self, touch, focus_x, focus_y, delta_x, velocity):
        if not self.dragging:
            # print("Pan")
            self.sendDataToClient("Pan", touch, None, [("deltaX", delta_x), ("vel", velocity)])
    
    def cgb_zoom(self, touch0, touch1, focus_x, focus_y, delta_scale):
        if not self.dragging:
            # print("Zoom")
            self.sendDataToClient("Zoom", touch0, touch1, [("centerPos", (focus_x, focus_y)), ("deltaScale", delta_scale)])
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
        dataDict["screenSize"] = (self.width, self.height)
        
        for pair in otherData:
            dataDict[pair[0]] = pair[1]
        
        return dataDict
    
    def sendDataToClient(self, type, touch0, touch1, otherData):
        if (self.clientSocket == None):
            return
        
        data = self.compileDataIntoJson(type, touch0,touch1, otherData)

        jsobObj = json.dumps(data, indent = 4)
        
        self.clientSocket.send(jsobObj.encode('utf-8'))
    #endregion

class PenInputApp(App):
    clientSocket = None
    stopping = False
    
    def build(self):
        self.sm = ScreenManager()
        
        self.host = str(socket.gethostbyname(socket.gethostname()))
        self.port = 9090
        
        print("Server started at: " + self.host + " on port: " + str(self.port))
        
        self.inputWidget = InputWidget(hostIP = self.host, hostPort = str(self.port))
        Window.bind(mouse_pos = self.inputWidget.on_mouse_pos)
        
        self.sm.add_widget(self.inputWidget)
        
        self.waitThread = threading.Thread(target = self.waitConnect)
        self.waitThread.start()
        
        return self.sm
        
    def on_stop(self):
        if self.clientSocket != None:
            self.clientSocket.close()
        
        self.stopping = True
    
    def waitConnect(self):
        s = socket.socket()
        s.bind((self.host, self.port))
        
        print("Waiting for client to connect")
        
        s.listen(1)
        
        self.clientSocket, addr = s.accept()
        
        # Get connection info (client ip, port, client name)
        info = self.clientSocket.getpeername()
        clientName = socket.getfqdn(info[0])
        
        print("Connection from: " + str(info) + ", " + str(clientName))
        
        self.inputWidget.clientSocket = self.clientSocket
        
        print("Client is ready. Starting to send input data")

if __name__ == "__main__":
    PenInputApp().run()