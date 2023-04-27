import os
os.environ['KIVY_NO_CONSOLELOG'] = '1'

import socket
import pyautogui
import time
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.config import Config
from kivy.core.window import Window
import threading

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

class InputWidget(Label):
    clientSocket = None
    
    def __init__(self, hostIP, hostPort, **kwargs):
        Label.__init__(self, text = "Host IP: " + hostIP + "     Host Port: " + hostPort, **kwargs)
        pass
    
    def touchInfo(self, touch):
        info = str(touch.pos[0] / self.width) + "," + str(touch.pos[1] / self.height) + "," + str(touch.button) + "," + str(touch.device) + "," + str(touch.is_mouse_scrolling) + "," + str(touch.is_double_tap) + "," + str(touch.is_triple_tap) + ","
        
        if (touch.shape != None):
            info += str(touch.shape.width) + "," + str(touch.shape.height)
        else:
            info += "None"
        
        return info
    
    def on_mouse_pos(self, instance, pos):
        if (self.clientSocket == None):
            return
        
        data = "Move:" + str(pos[0] / self.width) + "," + str(pos[1] / self.height) + ",None,mouseHover,False,False,False,None" + "\n"
    
        self.clientSocket.send(data.encode('utf-8'))
    
    def on_touch_down(self, touch):
        if (self.clientSocket == None):
            return
        
        data = "Down:" + self.touchInfo(touch) + "\n"
        
        self.clientSocket.send(data.encode('utf-8'))
        
    def on_touch_move(self, touch):
        if (self.clientSocket == None):
            return
        
        data = "Move:" + self.touchInfo(touch) + "\n"
        
        self.clientSocket.send(data.encode('utf-8'))
    
    def on_touch_up(self, touch):
        if (self.clientSocket == None):
            return
        
        data = "Up:" + self.touchInfo(touch) + "\n"
        
        self.clientSocket.send(data.encode('utf-8'))

class PenInputApp(App):
    clientSocket = None
    stopping = False
    
    def build(self):        
        self.host = str(socket.gethostbyname(socket.gethostname()))
        self.port = 9090
        self.inputWidget = InputWidget(hostIP = self.host, hostPort = str(self.port))
        
        Window.bind(mouse_pos = self.inputWidget.on_mouse_pos)
        
        self.waitThread = threading.Thread(target = self.waitConnect)
        self.waitThread.start()
        
        return self.inputWidget
        
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