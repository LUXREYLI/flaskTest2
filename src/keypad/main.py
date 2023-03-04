import requests
from requests.structures import CaseInsensitiveDict
import json
from keypad import keypad

if __name__ == '__main__':
    # Initialize
    kp = keypad()

    url = "http://localhost:8000/physicalkeypad"

    while True:
        # wait a keypress
        digit = kp.getKey()

        # format the keystroke to json string and pass it to the webapp
        #jsonString = json.loads('{"keystroke": "' + digit + '"}')
        #res = requests.post('http://localhost:8000/physicalkeypad', json=jsonString)




        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        data = '{"keystroke": "' + digit + '"}'
        res = requests.post(url, headers=headers, data=data)

        print('response from server:', res.text)
