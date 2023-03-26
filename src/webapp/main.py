from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from email_validator import validate_email, EmailNotValidError
from datetime import timedelta, datetime, timezone
from decouple import config
from models import db, Account, Parameter
import constant
import threading
import re
import bcrypt
import RPi.GPIO as GPIO

# database connection string
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
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize the app with the extension
db.init_app(app)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(constant.LOCK_PIN, GPIO.OUT)
GPIO.setup(constant.ALERT_PIN, GPIO.OUT)


# function to close the lock again after X seconds
def CloseLock():
    GPIO.output(constant.LOCK_PIN, GPIO.LOW)
    print('Off...')


# function to handle the keypadtimezone
def KeypadHandler(actionValue, softKeypad):
    localBuf = ''
    if actionValue in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'A', 'B', 'C', 'D', '#']:
        actionValidated = False

        if not 'startTime' in session:
            if actionValue in ['A', 'B', 'C', 'D']:
                # check if the user is initialized
                myData = db.session.get(Account, actionValue)
                if not myData.initialized and myData.password is None:
                    # the user is not configured
                    localBuf = 'Not config.'
                elif not myData.initialized:
                    localBuf = 'Init - ' + actionValue
                else:
                    # save start moment (Aware Datetime -> https://docs.python.org/3/library/datetime.html)
                    session['startTime'] = datetime.now(timezone.utc)
                    actionValidated = True
            else:
                localBuf = 'Error'
        else:
            diffInSeconds = (datetime.now(timezone.utc) -
                             session['startTime']).total_seconds()
            if diffInSeconds > constant.LOCK_TIMEOUT:
                localBuf = 'Timeout'
            else:
                actionValidated = True

        if actionValidated:
            if 'buffer' in session:
                localBuf = session['buffer']
            localBuf = localBuf + actionValue
            session['buffer'] = localBuf

            if actionValue == '#' and len(localBuf) == 7:
                # read data of user account
                myData = db.session.get(Account, localBuf[:1])

                # check the current password with the saved password
                currentPwd = localBuf[2:-1]
                if bcrypt.checkpw(currentPwd.encode('utf-8'), myData.password):
                    # check if thread always running
                    isThreadRunning = False
                    for thread in threading.enumerate():
                        if thread.name == 'Thread_CloseLock':
                            isThreadRunning = True

                    if not isThreadRunning:
                        GPIO.output(constant.LOCK_PIN, GPIO.HIGH)

                        # output on console
                        print('On...')

                        # start a thread to close again after 10 sec.
                        thread = threading.Timer(10, CloseLock)
                        thread.name = 'Thread_CloseLock'
                        thread.start()

                        # clear the session
                        session.clear()
                    else:
                        # clear the session
                        session.clear()

                        # output on console
                        print('Always on...')
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


# home route that redirects to softkeypad
@app.route("/")
def home():
    return redirect("/softkeypad")


# entry point for the soft keypad
@app.route("/softkeypad", methods=['GET', 'POST'])
def softkeypad():
    localBuf = ''
    if request.method == 'POST':
        actionValue = request.form.get('action')
        localBuf = KeypadHandler(actionValue, True)

    if localBuf[0:7] == 'Init - ':
        # initialize the user
        return redirect(url_for('pincode', mode=3, user=localBuf[7:]))

    return render_template('softkeypad.html', content=localBuf)


# entry point for the physical keypad
@app.route("/physicalkeypad", methods=['POST'])
def physicalkeypad():
    inputJson = request.get_json()
    actionValue = inputJson['keystroke']
    localBuf = KeypadHandler(actionValue, False)

    returnValue = {'answer': localBuf}
    return jsonify(returnValue)


@app.route("/admin", methods=['GET'])
def admin():
    if not 'adminMode' in session:
        # not in admin-mode
        myData = db.session.get(Parameter, 1)
        if not myData.initialized:
            # masterpassword is not known
            return redirect(url_for('pincode', mode=1))
        else:
            return redirect(url_for('pincode', mode=2))

    return redirect(url_for('accounts'))


@app.route("/accounts", methods=['GET', 'POST'])
def accounts():
    if not 'adminMode' in session:
        # not in admin-mode
        return redirect(url_for('admin'))

    if request.method == 'POST':
        actionValue = request.form.get('action')
        if actionValue in ['Reset_A', 'Reset_B', 'Reset_C', 'Reset_D']:
            # reset account informations
            accountId = actionValue[6:]
            myData = db.session.get(Account, accountId)
            myData.email = accountId.lower() + '@unknown.com'
            myData.password = None
            myData.initialized = False
            db.session.commit()
        elif actionValue in ['Set_A', 'Set_B', 'Set_C', 'Set_D']:
            # identify the user
            accountId = actionValue[4:]

            # check the email
            email = request.form.get('mail_' + accountId)
            try:
                email = validate_email(email).email
            except EmailNotValidError as e:
                print(str(e))

            # set account informations
            myData = db.session.get(Account, accountId)
            myData.email = request.form.get('mail_' + accountId)

            # set new password and convert string to byte
            pwd = request.form.get('password_' + accountId)
            bytePwd = pwd.encode('utf-8')

            # generate a new salt
            mySalt = bcrypt.gensalt()

            # hash password and save the hash
            myData.password = bcrypt.hashpw(bytePwd, mySalt)
            db.session.commit()

    # get all data from table 'account'
    myData = db.session.query(Account).order_by(Account.account_id)
    return render_template('accounts.html', accounts=myData)


@app.route("/onoff", methods=['GET', 'POST'])
def onoff():
    if request.method == 'POST':
        if request.form.get('action') == 'ON':
            GPIO.output(constant.LOCK_PIN, GPIO.HIGH)
            GPIO.output(constant.ALERT_PIN, GPIO.HIGH)

            # output on console
            print("On...")
        elif request.form.get('action') == 'OFF':
            GPIO.output(constant.LOCK_PIN, GPIO.LOW)
            GPIO.output(constant.ALERT_PIN, GPIO.LOW)
        else:
            pass  # unknown
    return render_template('onoff.html')


@app.route("/pincode", methods=['GET', 'POST'])
def pincode():
    # the mode must be specified
    #   mode=1 --> 2 controls to set the masterpassword
    #   mode=2 --> 1 control to enter in admin mode
    #   mode=3 --> 3 controls to change password
    modeOfPinCode = request.args.get('mode')
    message = None

    if request.method == 'GET':
        if modeOfPinCode == '3' and not 'initializeUser' in session:
            # save the user in the session
            session['initializeUser'] = request.args.get('user')
    elif request.method == 'POST':
        if modeOfPinCode == '1':
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
        elif modeOfPinCode == '2':
            adminPwd = request.form.get('AdminPassword')
            if adminPwd != '':
                # read data of parameter
                myData = db.session.get(Parameter, 1)

                # check the password with the saved password
                if bcrypt.checkpw(adminPwd.encode('utf-8'), myData.password):
                    session['adminMode'] = True
                    return redirect(url_for('accounts'))

            message = 'Wrong Password. Try again.'
        elif modeOfPinCode == '3':
            initializeUser = session['initializeUser']

            if not initializeUser is None:
                currentPwd = request.form.get('CurrentPassword')
                newPwd = request.form.get('NewPassword')
                print(initializeUser)
                print(currentPwd)
                print(newPwd)
                if currentPwd != '' and newPwd != '' and newPwd == request.form.get('ConfirmPassword'):
                    # read data of user account
                    myData = db.session.get(Account, initializeUser)

                    # check the current password with the saved password
                    currentPwd = request.form.get('CurrentPassword')
                    if bcrypt.checkpw(currentPwd.encode('utf-8'), myData.password):
                        # convert string to byte
                        bytePwd = newPwd.encode('utf-8')

                        # generate a new salt
                        mySalt = bcrypt.gensalt()

                        # hash password and save the hash
                        myData.password = bcrypt.hashpw(bytePwd, mySalt)
                        myData.initialized = True
                        db.session.commit()

                        # delete the user from the session
                        session.pop('initializeUser', None)

                        return redirect(url_for('softkeypad'))
                    else:
                        message = 'Wrong Password. Try again.'
                else:
                    message = 'Wrong Password. Try again.'
            else:
                return redirect(url_for('softkeypad'))

    if modeOfPinCode == '1':
        listOfControls = {1: {'controlName': 'NewPassword',
                              'label': 'New password'},
                          2: {'controlName': 'ConfirmPassword',
                              'label': 'Confirm password'}}
    elif modeOfPinCode == '2':
        listOfControls = {1: {'controlName': 'AdminPassword',
                              'label': 'Admin password'}}
    elif modeOfPinCode == '3':
        listOfControls = {1: {'controlName': 'CurrentPassword',
                              'label': 'Current password'},
                          2: {'controlName': 'NewPassword',
                              'label': 'New password'},
                          3: {'controlName': 'ConfirmPassword',
                              'label': 'Confirm password'}}
    else:
        listOfControls = None

    return render_template('pincode.html', mode=modeOfPinCode, controls=listOfControls, message=message)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=config('DEBUG', cast=bool))
