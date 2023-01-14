import time
import requests
import json
from keypad import keypad

if __name__ == '__main__':
    # Initialize
    kp = keypad()

    while True:
        # wait a keypress
        digit = None
        while digit == None:
            digit = kp.getKey()
        time.sleep(0.5)

        print(digit)

        # format the keystroke to json and pass it to the webapp
        jsonString = json.dumps({'keystroke': digit})
        res = requests.post('http://localhost:8000/test', json=jsonString)
        print('response from server:', res.text)
