import socket
import pyautogui
import time
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.config import Config
from kivy.core.window import Window

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

class InputWidget(Widget):
    clientSocket = None
    
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
    
        clientSocket.send(data.encode('utf-8'))
    
    def on_touch_down(self, touch):
        if (self.clientSocket == None):
            return
        
        data = "Down:" + self.touchInfo(touch) + "\n"
        
        clientSocket.send(data.encode('utf-8'))
        
    def on_touch_move(self, touch):
        if (self.clientSocket == None):
            return
        
        data = "Move:" + self.touchInfo(touch) + "\n"
        
        clientSocket.send(data.encode('utf-8'))
    
    def on_touch_up(self, touch):
        if (self.clientSocket == None):
            return
        
        data = "Up:" + self.touchInfo(touch) + "\n"
        
        clientSocket.send(data.encode('utf-8'))

class PenInputApp(App):

    def build(self):        
        self.inputWidget = InputWidget()
        
        Window.bind(mouse_pos = self.inputWidget.on_mouse_pos)
        
        return self.inputWidget

    def on_start(self):
        host = input("Enter this device's ip address: ")
        port = 8080
        
        s = socket.socket()
        s.bind((host, port))
        
        print("Waiting for client to connect")
        
        s.listen(1)
        
        global clientSocket
        clientSocket, addr = s.accept()
        
        # Get connection info (client ip, port, client name)
        info = clientSocket.getpeername()
        clientName = socket.getfqdn(info[0])
                
        print("Connection from: " + str(info) + ", " + str(clientName))
        
        self.inputWidget.clientSocket = clientSocket
        
        print("Client is ready. Starting to send input data")

    def on_stop(self):
        global clientSocket
        clientSocket.close()

if __name__ == "__main__":
    PenInputApp().run()


# data = clientSocket.recv(1024).decode('utf-8')

# if not data:
#     break

# print('From online user: ' + data)

# if data == "stop":
#     print("Recieved stop message. Closing connection.")
#     quitMessage = "disconnected by server"
#     clientSocket.send(quitMessage.encode('utf-8'))
#     running = False
#     break
