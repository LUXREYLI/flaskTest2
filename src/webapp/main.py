from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from datetime import timedelta, datetime, timezone
from decouple import config
from models import db, Account, Parameter
import constant
import threading
import re
import bcrypt
import RPi.GPIO as GPIO

# Database connection string
DB_URL = 'postgresql://{user}:{pw}@{url}:{port}/{db}'.format(
    user=config('POSTGRES_USER'),
    pw=config('POSTGRES_PASSWORD'),
    url=config('POSTGRES_SERVER'),
    port=config('POSTGRES_PORT'),
    db=config('POSTGRES_DB'))

# create the flask app
app = Flask(__name__)
app.secret_key = config('SECRET_KEY')
app.permanent_session_lifetime = timedelta(
    seconds=config('SESSION_LIFETIME', cast=int))
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize the app with the extension
db.init_app(app)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(constant.LOCK_PIN, GPIO.OUT)

# function to close the lock again after X seconds
def CloseLock():
    # switch off the led
    GPIO.output(constant.LOCK_PIN, GPIO.LOW)
    print('Ausgeschaltet...')

# function to handle the keypad
def KeypadHandler(actionValue):
    localBuf = ''
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
            session['buffer'] = localBuf

            if actionValue == '#' and len(localBuf) == 7:
                if localBuf == 'A#4567#':
                    # Check if thread always running
                    isThreadRunning = False
                    for thread in threading.enumerate():
                        if thread.name == 'Thread_CloseLock':
                            isThreadRunning = True

                    if not isThreadRunning:
                        GPIO.output(constant.LOCK_PIN, GPIO.HIGH)

                        # Ausgabe auf Console
                        print('Eingeschaltet...')

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
                        print('Immer noch offen...')
            elif len(localBuf) > 7:
                localBuf = 'Error'
                # clear the session
                session.clear()

            # replace all digits with '-'
            localBuf = re.sub(r'\d', '-', localBuf)
        else:
            # clear the session
            session.clear()
    elif actionValue == '*':
        # clear the session
        session.clear()
        # switch off the led
        GPIO.output(constant.LOCK_PIN, GPIO.LOW)
    else:
        pass  # unknown

    return localBuf


# soft keypad
@app.route("/", methods=['GET', 'POST'])
def keypad():
    localBuf = ''
    if request.method == 'POST':
        actionValue = request.form.get('action')
        localBuf = KeypadHandler(actionValue)

    return render_template('keypad.html', content=localBuf)


# physical keypad
@app.route("/physicalkeypad", methods=['POST'])
def physicalkeypad():
    inputJson = request.get_json()
    actionValue = inputJson['keystroke']
    localBuf = KeypadHandler(actionValue)

    returnValue = {'answer': localBuf}
    return jsonify(returnValue)


@app.route("/onoff", methods=['GET', 'POST'])
def onoff():
    myData = db.session.get(Parameter, 1)
    if myData.initialized == False:
        # masterpassword is not known
        return redirect(url_for('setcode', mode=1))
    else:
        if request.method == 'POST':
            if request.form.get('action') == 'ON':
                GPIO.output(constant.LOCK_PIN, GPIO.HIGH)

                # Read data of account B
                # old method --> myData = Account.query.get('B')
                # https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#overview
                myData = db.session.get(Account, 'B')

                if myData.password is None:
                    # set new password and convert string to byte
                    pwd = '1234'
                    bytePwd = pwd.encode('utf-8')

                    # generate a new salt
                    mySalt = bcrypt.gensalt()

                    # hash password qnd save the hash
                    myData.password = bcrypt.hashpw(bytePwd, mySalt)
                    db.session.commit()

                    print(myData.password)
                else:
                    print('Pwd Check...')
                    print(bcrypt.checkpw(b'1234', myData.password))
                    print(bcrypt.checkpw(b'5678', myData.password))

                # Ausgabe auf Console
                print("Eingeschlatet...")
            elif request.form.get('action') == 'OFF':
                GPIO.output(constant.LOCK_PIN, GPIO.LOW)
            else:
                pass  # unknown
        return render_template('onoff.html')


@app.route("/setcode", methods=['GET', 'POST'])
def setcode():
    # The mode must be specified
    #   mode=1 --> 2 controls to set the masterpassword
    #   mode=2 --> 3 controls
    modeOfSetCode = request.args.get('mode')
    message = None

    if request.method == 'POST':
        print(modeOfSetCode)
        if modeOfSetCode == '1':
            newPwd = request.form.get('NewPassword')
            if newPwd != '' and newPwd == request.form.get('ConfirmPassword'):
                # convert string to byte
                bytePwd = newPwd.encode('utf-8')

                # generate a new salt
                mySalt = bcrypt.gensalt()

                # hash password and save the hash
                myData = db.session.get(Parameter, 1)
                myData.password = bcrypt.hashpw(bytePwd, mySalt)
                myData.initialized = True
                db.session.commit()

                return redirect(url_for('onoff', mode=1))
            else:
                message = 'Wrong Password. Try again.'

    if modeOfSetCode == '1':
        listOfControls = {1: {'controlName': 'NewPassword',
                              'label': 'New password'},
                          2: {'controlName': 'ConfirmPassword',
                              'label': 'Confirm password'}}
    elif modeOfSetCode == '3':
        listOfControls = {1: {'controlName': 'CurrentPassword',
                              'label': 'Current password'},
                          2: {'controlName': 'NewPassword',
                              'label': 'New password'},
                          3: {'controlName': 'ConfirmPassword',
                              'label': 'Confirm password'}}
    else:
        listOfControls = None

    return render_template('setcode.html', mode=modeOfSetCode, controls=listOfControls, message=message)


@app.route("/accounts", methods=['GET', 'POST'])
def accounts():
    # get all data from table 'account'
    myData = db.session.query(Account).order_by(Account.account_id)

    return render_template('accounts.html', accounts=myData)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=config('DEBUG', cast=bool))
