import socket
import macmouse

pressed = False
dragging = False

startPos = (0, 0)
dragStart = (0, 0)

WIDTH = 1920
HEIGHT = 1080
SCROLL_SPEED = 1
TOUCH_DRAG_THRESHOLD = 0.1

def setCursorPos(x, y):
    global pressed, startPos
    
    localX = x * WIDTH
    localY = HEIGHT - (y * HEIGHT)
    
    curPos = macmouse.get_position()
    
    if curPos == (0, 0):
        print("FAILSAFE TRIGGERED! Mouse moved to top left corner")
        exit()
    elif curPos != (localX, localY) or pressed:
        if pressed:
            localY = y * -HEIGHT
            macmouse.move(startPos[0] + localX, startPos[1] + localY, absolute = True)
            # print("Moving by: " + str(localX) + ", " + str(startPos[1] + localY))
        else:
            macmouse.move(localX, localY, absolute = True)
            # print("Moving to: " + str(localX) + ", " + str(localY))

def move(pos, button, device, scrolling, doubleTap, tripleTap, shapeW, shapeH):
    global pressed, dragging
    
    pressed = device == "wm_pen" or device == "wm_touch"
    
    if device == "wm_touch":
        if pressed:            
            # Only drag if the touch moved enough
            if abs(float(pos[0]) - dragStart[0]) > TOUCH_DRAG_THRESHOLD or abs(float(pos[1]) - dragStart[1]) > TOUCH_DRAG_THRESHOLD:
                dragging = True
    
    x = float(pos[0]) - dragStart[0] if pressed else float(pos[0])
    y = float(pos[1]) - dragStart[1] if pressed else float(pos[1])
    
    setCursorPos(x, y)

def down(pos, button, device, scrolling, doubleTap, tripleTap, shapeW, shapeH):
    global pressed, startPos, dragStart
    
    if device == "wm_pen" or device == "wm_touch":
        if not pressed:
            startPos = macmouse.get_position()
            dragStart = (float(pos[0]), float(pos[1]))
        
        pressed = True
    else:
        pressed = False
    
    if device == "wm_pen":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.press(button = 'left')
    elif button == "left":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.press(button = 'left')
    elif button == "right":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.press(button = 'right')
    elif button == "middle":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.press(button = 'middle')
    elif button == "scrolldown":
        macmouse.wheel(SCROLL_SPEED)
    elif button == "scrollup":
        macmouse.wheel(-SCROLL_SPEED)

def up(pos, button, device, scrolling, doubleTap, tripleTap, shapeW, shapeH):
    global pressed, dragging
    
    if device == "wm_touch" and not dragging:
        if doubleTap == "True":
            macmouse.click(button = 'right')
        elif tripleTap == "True":
            macmouse.click(button = 'middle')
        else:
            macmouse.click(button = 'left')
    elif button == "None" or device == "wm_pen":
        macmouse.release(button = 'left')
    elif button == "left":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.release(button = 'left')
    elif button == "right":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.release(button = 'right')
    elif button == "middle":
        setCursorPos(float(pos[0]), float(pos[1]))
        macmouse.release(button = 'middle')
    
    if device == "wm_pen" or device == "wm_touch":
        pressed = False
        dragging = False
    
def processData(inputStr):
    # print(inputStr)
    lines = inputStr.split("\n")
        
    for line in lines:
        if line == '':
            continue
        
        split = line.split(":")
        
        if len(split) < 2:
            continue
        
        inputType = split[0]
        inputData = split[1].split(",")
        
        if len(inputData) < 8:
            continue
        
        try:
            pos = (inputData[0], inputData[1])
            button = inputData[2]
            device = inputData[3]
            scrolling = inputData[4]
            doubleTap = inputData[5]
            tripleTap = inputData[6]
            shapeW = 0
            shapeH = 0
            
            if inputData[7] != "None":
                shapeW = inputData[7]
                shapeH = inputData[8]
            
            if inputType == "Move":
                move(pos, button, device, scrolling, doubleTap, tripleTap, shapeW, shapeH)
            elif inputType == "Down":
                down(pos, button, device, scrolling, doubleTap, tripleTap, shapeW, shapeH)
            elif inputType == "Up":
                up(pos, button, device, scrolling, doubleTap, tripleTap, shapeW, shapeH)
        except Exception as e:
            print("Error parsing line: '" + str(line) + "' with error message: " + str(e))

def client():
    host = input("Enter server IP: ")
    port = int(input("Enter server port: "))
    
    print("Looking for server")
    
    serverSocket = socket.socket()
    serverSocket.connect((host, port))
    
    print("Connected to server: " + host + ":" + str(port))
    
    running = True
    
    while running == True:
        data = serverSocket.recv(1024).decode('utf-8')
        
        if not data:
            break
        
        processData(data)
    
    print("Connection closed by server")
    
    serverSocket.close()

if __name__ == '__main__':
    client()