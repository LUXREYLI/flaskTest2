import requests
from requests.structures import CaseInsensitiveDict
import json
from keypad import keypad

if __name__ == '__main__':
    # Initialize
    kp = keypad()

    webAppUrl = 'http://localhost:8000/physicalkeypad'

    isCookieKnown = False
    while True:
        # wait a keypress
        digit = kp.getKey()

        # prepare the header
        if isCookieKnown == True:
            headers = setCookieValue
        else:
            headers = CaseInsensitiveDict()
        headers['Content-Type'] = 'application/json'

        # prepare the data to transfer
        data = '{"keystroke": "' + digit + '"}'

        # make the POST request
        res = requests.post(webAppUrl, headers=headers, data=data)

        # cache the answer for 'Set-Cookie'
        setCookieValue = {'Cookie': res.headers['Set-Cookie']}
        isCookieKnown = True

        print('response from server:', res.text)
