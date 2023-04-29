import os
os.environ['KIVY_NO_CONSOLELOG'] = '1'

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
    
    touchDrag = False
    
    def __init__(self, hostIP, hostPort, **args):
        super().__init__(**args)
        
        self.label = Label(text = "Host IP: " + hostIP + "     Host Port: " + hostPort)
        
        self.add_widget(self.label)
    
    #region Input Methods
    # def on_mouse_pos(self, instance, pos):
    #     if (self.clientSocket == None):
    #         return
        
    #     data = "Move:" + str(pos[0] / self.width) + "," + str(pos[1] / self.height) + ",None,mouseHover,False,False,False,None" + "\n"
    
    #     self.clientSocket.send(data.encode('utf-8'))
    
    # def on_touch_down(self, touch):
    #     if (self.clientSocket == None):
    #         return
        
    #     data = "Down:" + self.touchInfo(touch) + "\n"
        
    #     self.clientSocket.send(data.encode('utf-8'))
        
    # def on_touch_move(self, touch):
    #     if (self.clientSocket == None):
    #         return
        
    #     data = "Move:" + self.touchInfo(touch) + "\n"
        
    #     self.clientSocket.send(data.encode('utf-8'))
    
    # def on_touch_up(self, touch):
    #     if (self.clientSocket == None):
    #         return
        
    #     data = "Up:" + self.touchInfo(touch) + "\n"
        
    #     self.clientSocket.send(data.encode('utf-8'))
    
    
    def cgb_select(self, touch, focus_x, focus_y, long_press):        
        print("Select: " + str(long_press))
        
        self.sendDataToClient("SelectDown", touch, focus_x, focus_y, None, [("longPress", long_press)])
    
    def cgb_long_press_end(self, touch, focus_x, focus_y):
        if (self.touchDrag):
            print("drag ended")
            self.touchDrag = False
        else:
            print("long press end")
            
            self.sendDataToClient("SelectLongUp", touch, focus_x, focus_y, None, [])
    
    def cgb_drag(self, touch, focus_x, focus_y, delta_x, delta_y):
        self.touchDrag = True
        
        self.sendDataToClient("Drag", touch, focus_x, focus_y, None, [("deltaX", delta_x), ("deltaY", delta_y)])
    
    def cgb_scroll(self, touch, focus_x, focus_y, delta_y, velocity):
        self.sendDataToClient("Scroll", touch, focus_x, focus_y, None, [("deltaY", delta_y), ("vel", velocity)])
    
    def cgb_pan(self, touch, focus_x, focus_y, delta_x, velocity):
        self.sendDataToClient("Pan", touch, focus_x, focus_y, None, [("deltaX", delta_x), ("vel", velocity)])
    
    def cgb_zoom(self, touch0, touch1, focus_x, focus_y, delta_scale):
        self.sendDataToClient("Zoom", touch0, focus_x, focus_y, touch1, [("deltaScale", delta_scale)])
    #endregion
    
    #region Input Data
    # def touchInfo(self, touch, focusX, focusY):
    #     info = str(touch.pos[0] / self.width) + "," + str(touch.pos[1] / self.height) + "," + str(touch.button) + "," + str(touch.device) + "," + str(touch.is_mouse_scrolling) + "," + str(touch.is_double_tap) + "," + str(touch.is_triple_tap) + ","
        
    #     if (touch.shape != None):
    #         info += str(touch.shape.width) + "," + str(touch.shape.height)
    #     else:
    #         info += "None"
        
    #     return info
    
    def touchInfo(self, touch, x, y):
        if touch == None:
            return None
        
        infoDict = {
            "pos" : (x, y),
            "screenSize" : (self.width, self.height),
            "button" : touch.button,
            "device" : touch.device,
            "shape" : (touch.shape.width, touch.shape.height) if touch.shape != None else None
        }
        
        return str(infoDict)

    def compileDataIntoJson(self, type, touch0, x, y, touch1, otherData):
        dataDict = {}
        
        dataDict['type'] = type
        dataDict['touch0'] = self.touchInfo(touch0, x, y)
        dataDict['touch1'] = self.touchInfo(touch1, x, y)
        dataDict['x'] = x
        dataDict['y'] = y
        
        for pair in otherData:
            dataDict[pair[0]] = pair[1]
        
        return dataDict
    
    def sendDataToClient(self, type, touch0, x, y, touch1, otherData):
        # data = self.compileDataIntoJson(type, touch0, x, y, touch1, otherData)
        
        # print(data)
        
        if (self.clientSocket == None):
            return
        
        data = self.compileDataIntoJson(type, touch0, x, y, touch1, otherData)

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
        
        self.inputWidget = InputWidget(hostIP = self.host, hostPort = str(self.port))
        
        self.sm.add_widget(self.inputWidget)
        # Window.bind(mouse_pos = self.inputWidget.on_mouse_pos)
        
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