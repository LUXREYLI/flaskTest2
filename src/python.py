from flask import Flask, render_template, request, session
from datetime import timedelta, datetime, timezone
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import os
import threading
import RPi.GPIO as GPIO

# take environment variables from .env   
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.permanent_session_lifetime = timedelta(seconds=10)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)


def CloseLock():
    # switch off the led
    GPIO.output(18, GPIO.LOW)
    print('Ausgeschaltet...')


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('action') == 'ON':
            GPIO.output(18, GPIO.HIGH)
            # Ausgabe auf Console
            print("Eingeschlatet...")
        elif request.form.get('action') == 'OFF':
            GPIO.output(18, GPIO.LOW)
        else:
            pass  # unknown
    return render_template('index.html')


# Keypad
@app.route("/keypad", methods=['GET', 'POST'])
def keypad():
    localBuf = ''
    if request.method == 'POST':
        actionValue = request.form.get('action')
        if actionValue in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'A', 'B', 'C', 'D', '#']:

            if not 'startTime' in session:
                if actionValue in ['A', 'B', 'C', 'D']:
                    # save start moment (Aware Datetime -> https://docs.python.org/3/library/datetime.html)
                    session['startTime'] = datetime.now(timezone.utc)
                else:
                    localBuf = 'Error'
            else:
                diffInSeconds = (datetime.now(timezone.utc) -
                                 session['startTime']).total_seconds()

                print(diffInSeconds)
                if diffInSeconds > 15:
                    localBuf = 'Timeout'

            if localBuf != 'Error' and localBuf != 'Timeout':
                if 'buffer' in session:
                    localBuf = session['buffer']
                localBuf = localBuf + actionValue
                session["buffer"] = localBuf

                if actionValue == '#' and len(localBuf) == 7:
                    if localBuf == 'A#4567#':
                        # Check if thread always running
                        isThreadRunning = False
                        for thread in threading.enumerate():
                            if thread.name == 'Thread_CloseLock':
                                isThreadRunning = True

                        if not isThreadRunning:
                            GPIO.output(18, GPIO.HIGH)

                            # Ausgabe auf Console
                            print("Eingeschaltet...")

                            # Start a thread to close again after 10 sec.
                            thread = threading.Timer(10, CloseLock)
                            thread.name = 'Thread_CloseLock'
                            thread.start()

                            # clear the session
                            session.clear()
                        else:
                            # clear the session
                            session.clear()

                            # Ausgabe auf Console
                            print("Immer noch offen...")
                elif len(localBuf) > 7:
                    localBuf = 'Error'
                    # clear the session
                    session.clear()
            else:
                # clear the session
                session.clear()
        elif actionValue == '*':
            # clear the session
            session.clear()
            # switch off the led
            GPIO.output(18, GPIO.LOW)
        else:
            pass  # unknown
    return render_template('keypad.html', content=localBuf)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=os.environ.get('DEBUG'))
