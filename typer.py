from pynput.keyboard import Key, Controller
import time
import random
import keyboard as kb

delayVariation = 0.1
spaceVariation = 0.6
newLineVariation = 1.2

toType = """"""

charArray = list(toType)

keyboard = Controller()

print("Starting in 5 seconds")

time.sleep(5)

print("Starting to type")

for char in charArray:
    if char == "\n":
        keyboard.tap(Key.enter)
    else:
        keyboard.tap(char)
        
    if char == " ":
        time.sleep(random.random() * spaceVariation)
    if char == "\n":
        time.sleep(random.random() * newLineVariation)
    else:
        time.sleep(random.random() * delayVariation)
    
    if kb.is_pressed('esc'):
        print("exiting")
        break