import socket
import os
import json
import pyautogui
import platform

try:
    import macmouse as ms
except:
    try:
        import mouse as ms
    except:
        print("Error loading macmouse (MacOS only) or mouse (Windows only) module. Please install one of them.")
        exit()

class PenClient():
    # Debug mode just makes the program print received data instead of manipulate the mouse
    DEBUG_MODE = False

    pressed = False
    dragging = False

    hasSettings = False

    startPos = (0, 0)
    dragStart = (0, 0)
    
    sourceScale = (1920, 1080)

    settingsDict = {
        "Width" : pyautogui.size()[0],
        "Height" : pyautogui.size()[1],
        "Mouse_Scroll_Speed" : 1,
        "Touch_Scroll_Speed" : 1,
        "Touch_Drag_Threshold" : 0.1,
        "Touch_Trackpad_Speed" : 1.0,
        "Enable_Failsafe" : True,
        "Last_IP" : "",
        "Last_Port" : 0,
    }

    def __init__(self, **kwargs):
        self.loadSavedSettings()
        self.client()

    #region Settings
    def loadSavedSettings(self):
        # Get local executable path
        path = os.path.dirname(os.path.realpath(__file__))
        settingsFilePath = path + "/settings.json"

        if not os.path.isfile(settingsFilePath):
            self.setVarsFromSettingsDict(self.settingsDict)
            return

        print("Loading settings")

        with open(settingsFilePath, 'r') as settingsfile:
            # Reading from json file
            settingsJsonObject = json.load(settingsfile)

            settingsfile.close()

        self.settingsDict = settingsJsonObject

        self.setVarsFromSettingsDict(settingsJsonObject)

        self.hasSettings = True

        print("Loaded settings")

    def setVarsFromSettingsDict(self, settingsDict):
        print(str(settingsDict))
        self.WIDTH = settingsDict["Width"]
        self.HEIGHT = settingsDict["Height"]
        self.MOUSE_SCROLL_SPEED = settingsDict["Mouse_Scroll_Speed"]
        self.TOUCH_SCROLL_SPEED = settingsDict["Touch_Scroll_Speed"]
        self.TOUCH_DRAG_THRESHOLD = settingsDict["Touch_Drag_Threshold"]
        self.TOUCH_TRACKPAD_SPEED = settingsDict["Touch_Trackpad_Speed"]
        self.ENABLE_FAILSAFE = settingsDict["Enable_Failsafe"]
        self.lastIP = settingsDict["Last_IP"]
        self.lastPort = settingsDict["Last_Port"]

    def saveSettings(self, notify = True):
        # Get local executable path
        path = os.path.dirname(os.path.realpath(__file__))
        settingsFile = path + "/settings.json"

        # Serializing json
        jsonObject = json.dumps(self.settingsDict, indent = 4)

        # Writing to sample.json
        with open(settingsFile, "w") as outfile:
            outfile.write(jsonObject)

            outfile.close()

        if notify:
            print("Saved settings")

    def saveAddressAndPort(self, address, port):
        self.settingsDict["Last_IP"] = address
        self.settingsDict["Last_Port"] = port

        self.saveSettings(False)
    #endregion

    #region Computer Input
    def setCursorPos(self, pos):
        localPos = pos

        curPos = ms.get_position()
        
        # Check if the resoltion changed for some reason
        curSize = pyautogui.size()
        if curSize[0] != self.WIDTH or curSize[1] != self.HEIGHT:
            self.WIDTH = curSize[0]
            self.HEIGHT = curSize[1]
            
            self.saveSettings(False)

        if curPos == (0, 0) and self.ENABLE_FAILSAFE:
            print("FAILSAFE TRIGGERED! Mouse moved to top left corner. This can be disabled in settings.txt")
            exit()
        elif curPos != localPos or self.pressed:
            if self.pressed:
                ms.move(self.startPos[0] + localPos[0], self.startPos[1] - localPos[1], absolute = True)
                # print("Moving by: " + str(localX) + ", " + str(startPos[1] + localY))
            else:
                ms.move(localPos[0], localPos[1], absolute = True)
                # print("Moving to: " + str(localX) + ", " + str(localY))

    def mouseMove(self, device, position):
        pos = self.remapPos(position)
        
        self.pressed = device == "wm_pen" or device == "wm_touch"

        deltaX = pos[0] - self.dragStart[0]
        deltaY = pos[1] - self.dragStart[1]
        
        print("Mouse move. dx: " + str(deltaX) + ", dy: " + str(deltaY))

        if device == "wm_touch":
            if self.pressed:
                # Only drag if the touch moved enough
                if deltaX**2 + deltaY**2 > self.TOUCH_DRAG_THRESHOLD:
                    self.dragging = True
                else:
                    deltaX = 0
                    deltaY = 0

        x = deltaX if self.pressed else pos[0]
        y = deltaY if self.pressed else pos[1]

        self.setCursorPos((x, y))

    # Simualate a click
    def click(self, button, touch):
        if self.DEBUG_MODE:
            if button == "left":
                print("Left click")
            elif button == "right":
                print("Right click")
        else:
            if touch["device"] == "mouse":
                if button == "left":
                    ms.click(button = 'left')
                elif button == "right":
                    ms.click(button = 'right')

    # Simualate a button press
    def mouseDown(self, button, touch):
        if self.DEBUG_MODE:
            print("Mouse down: " + button)
        else:
            device = touch["device"]
            
            if device == "wm_pen" or device == "wm_touch":
                if not self.pressed:
                    self.startPos = ms.get_position()
                    self.dragStart = self.remapPos(touch["pos"])

                self.pressed = True
            else:
                self.pressed = False
            
            ms.press(button = button)
    
    # Simualate a button release
    def mouseUp(self, button, touch):
        if self.DEBUG_MODE:
            print("Mouse up: " + button)
        else:
            device = touch["device"]
            
            if device == "wm_pen" or device == "wm_touch":
                self.pressed = False
                self.dragging = False
            
            ms.release(button = button)

    # Simulate horizontal and vertical scrolling
    def scroll(self, touch, deltaX, deltaY, velX, velY, originPos = None):
        pos = self.remapPos(touch["pos"] if originPos == None else originPos)

        mult = self.TOUCH_SCROLL_SPEED if touch["device"] == "wm_touch" else self.MOUSE_SCROLL_SPEED

        if self.DEBUG_MODE:
            print("Scrolling: " + str(deltaX) + ", " + str(deltaY) + " at " + str(pos) + " with velocity: " + str(velX) + ", " + str(velY))
        else:
            if deltaX != 0:
                pyautogui.hscroll(deltaX * mult, pos)

            if deltaY != 0:
                pyautogui.vscroll(deltaY * mult, pos)

    # Simualate zooming
    def zoom(self, touch, centerPos, deltaScale):
        centerPos = self.remapPos(centerPos)
        
        if self.DEBUG_MODE:
            print("Zooming: " + str(deltaScale) + " at " + str(centerPos))
        else:
            # If on mac, command + scroll to zoom
            if platform.system() == "Darwin":
                pyautogui.keyDown("command")
                self.scroll(touch, 0, deltaScale, 0, 1, centerPos)
                pyautogui.keyUp("command")
            else:
                # Otherwise, use ctrl + scroll
                pyautogui.keyDown("ctrl")
                self.scroll(touch, 0, deltaScale, 0, 1, centerPos)
                pyautogui.keyUp("ctrl")
    
    # Process data from the server
    def processData(self, inputStr):
        try:
            # Fix a weird bug where multiple JSON objects are sent at once
            if "}{" in inputStr:
                index = inputStr.index("}{")

                # Reprocess any other data after the }
                self.processData(inputStr[index + 1:])

                # Process the first part of the data
                inputStr = inputStr[:index + 1]

            jsonData = json.loads(inputStr)

            inputType = jsonData["type"]
            jsonData.pop("type")
            touch0 = jsonData["touch0"]
            jsonData.pop("touch0")
            touch1 = jsonData["touch1"]
            jsonData.pop("touch1")
            self.sourceSize = jsonData["screenSize"]
            jsonData.pop("screenSize")

            if inputType == "ClickPrimary":
                print("ClickPrimary: " + str(jsonData))

                self.click(button = 'left', touch = touch0)

            elif inputType == "ClickSecondary":
                print("ClickSecondary: " + str(jsonData))

                self.click(button = 'right', touch = touch0)

            elif inputType == "ClickMiddle":
                print("ClickMiddle: " + str(jsonData))
                
                self.click(button = 'middle', touch = touch0)

            elif inputType == "LongPressDown":
                # Only called when a long press drag STARTS!!
                
                # print("LongPressDrag Started: " + str(jsonData))
                
                if touch0["device"] != "mouse":
                    self.mouseDown(button = 'left', touch = touch0)
                    # print("Long press started")

            elif inputType == "LongPressUp":
                # print("LongPressUp: " + str(jsonData))
                
                if touch0["device"] != "mouse":
                    if jsonData["fromDrag"] == True:
                        self.mouseUp(button = 'left', touch = touch0)
                    else:
                        self.click(button = 'right', touch = touch0)

            elif inputType == "Drag":
                print("Drag: " + str(jsonData))
                
                if not self.dragging:
                    self.dragging = True
                    self.dragStart = self.remapPos(touch0["pos"])
                
                self.mouseMove(touch0["device"], touch0["pos"])

            elif inputType == "Scroll":
                # print("Scroll: " + str(jsonData))

                self.scroll(touch0, 0, jsonData["deltaY"], 0, jsonData["vel"])

            elif inputType == "Pan":
                # print("Pan: " + str(jsonData))

                self.scroll(touch0, jsonData["deltaX"], 0, jsonData["vel"], 0)

            elif inputType == "Zoom":
                # print("Zoom: " + str(jsonData))
                
                self.zoom(touch0, jsonData["centerPos"], jsonData["deltaScale"])

            elif inputType == "MouseHover":
                # print("MouseHover: " + str(jsonData))
                
                self.mouseMove("", jsonData["pos"])

        except Exception as e:
            print("\nError parsing input! Message: " + str(e) + "  \n:::  String: " + inputStr)
    #endregion

    #region Utils
    def remap(self, val, min1, max1, min2, max2):
        return min2 + (max2 - min2) * ((val - min1) / (max1 - min1))

    def remapPos(self, pos):
        return (self.remap(pos[0], 0, self.sourceSize[0], 0, self.WIDTH), self.remap(pos[1], 0, self.sourceSize[1], self.HEIGHT, 0))

    def askYesNoQuestion(self, question):
        answer = str.lower(input(question + " (y/n) "))

        yes = answer == "y" or answer == "yes"
        no = answer == "n" or answer == "no"

        if not yes and not no:
            print("Invalid input, type 'y' or 'yes' for YES, and 'n' or 'no' for NO.")
            return self.askYesNoQuestion(question)

        return yes
    #endregion
    
    
    def client(self):
        if self.hasSettings:
            print("Loaded saved IP: " + self.lastIP + " with port: " + str(self.lastPort))

            useOldVals = self.askYesNoQuestion("Use these values?")

            if useOldVals:
                host = self.lastIP
                port = self.lastPort
            else:
                host = input("Enter server IP: ")
                port = int(input("Enter server port: "))

                if self.askYesNoQuestion("Save these values?"):
                    self.saveAddressAndPort(host, port)
        else:
            print("No saved file found, please enter the server IP and port")
            host = input("Enter server IP: ")
            port = int(input("Enter server port: "))

            if self.askYesNoQuestion("Save these values?"):
                self.saveAddressAndPort(host, port)

        print("Looking for server")

        serverSocket = socket.socket()
        serverSocket.connect((host, port))

        print("Connected to server: " + host + ":" + str(port))

        running = True

        while running == True:
            try:
                data = serverSocket.recv(1024).decode('utf-8')
            except:
                print("Connection closed by server")
                break

            if not data:
                print("Connection closed by server")
                break

            self.processData(data)

        serverSocket.close()

        if self.askYesNoQuestion("Reconnect?"):
            print("")
            self.client()
        else:
            self.saveSettings()

if __name__ == '__main__':
    PenClient()