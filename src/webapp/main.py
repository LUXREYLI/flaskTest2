from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_mail import Mail, Message
from email_validator import validate_email, EmailNotValidError
from datetime import timedelta, datetime, timezone
from decouple import config
from random import randint
from models import db, Account, Parameter, LogInfo
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

# config for email
app.config['MAIL_SERVER'] = 'relay.proximus.be'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = config('MAIL_USER')
app.config['MAIL_PASSWORD'] = config('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# create an instance of the Mail class
mail = Mail(app)

# initialize the app with the extension
db.init_app(app)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(constant.LOCK_PIN, GPIO.OUT)
GPIO.setup(constant.ALERT_PIN, GPIO.OUT)


# function to close the lock again after X seconds
def CloseLock():
    GPIO.output(constant.LOCK_PIN, GPIO.LOW)
    print('Closed...')

    # manually push a context (-> https://flask.palletsprojects.com/en/2.2.x/appcontext/)
    with app.app_context():
        WriteLog(7)


# function to check if email already exists in account
def EmailExists(email):
    return db.session.query(Account.query.filter(Account.email == email).exists()).scalar()


# function to check if thread is already running
def IsThreadRunning():
    isThreadRunning = False
    for thread in threading.enumerate():
        if thread.name == 'Thread_CloseLock':
            isThreadRunning = True
    return isThreadRunning


# function to open the lock
def OpenLock(accountId=None):
    GPIO.output(constant.LOCK_PIN, GPIO.HIGH)

    # output on console
    print('Open...')

    # write to logInfo
    WriteLog(1, accountId)

    # start a thread to close again after 5 sec.
    thread = threading.Timer(5, CloseLock)
    thread.name = 'Thread_CloseLock'
    thread.start()


# function to handle the keypadtimezone
def KeypadHandler(actionValue):
    localBuf = ''
    if actionValue in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'A', 'B', 'C', 'D', '#', 'X']:
        actionValidated = False

        if actionValue == 'X':
            # check if thread is already running
            if not IsThreadRunning():
                OpenLock()
            else:
                # output on console
                print('Already open...')

                # write to logInfo
                WriteLog(2)
        elif not 'startTime' in session:
            if actionValue in ['A', 'B', 'C', 'D']:
                # check if the user is initialized
                myData = db.session.get(Account, actionValue)
                GPIO.output(constant.ALERT_PIN, GPIO.LOW)
                if not myData.initialized and myData.password is None:
                    # the user is not configured
                    localBuf = 'Not config.'
                    GPIO.output(constant.ALERT_PIN, GPIO.HIGH)
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
                    # check if thread is already running
                    if not IsThreadRunning():
                        OpenLock(localBuf[:1])

                        # clear the session
                        session.clear()
                    else:
                        # clear the session
                        session.clear()

                        # output on console
                        print('Already open...')

                        # write to logInfo
                        WriteLog(2, localBuf[:1])
                else:
                    # write to logInfo
                    WriteLog(3, localBuf[:1])
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
        # switch off
        GPIO.output(constant.LOCK_PIN, GPIO.LOW)
        GPIO.output(constant.ALERT_PIN, GPIO.LOW)
    else:
        pass  # unknown

    return localBuf


# function to write to logInfoinfo
def WriteLog(messageId, accountId=None):
    if messageId == 1:
        message = 'Successfully opened'
    elif messageId == 2:
        message = 'Already open'
    elif messageId == 3:
        message = 'Wrong password'
    elif messageId == 4:
        message = 'Reset account'
    elif messageId == 5:
        message = 'Set account information'
    elif messageId == 6:
        message = 'Initialize account'
    elif messageId == 7:
        message = 'Closed'
    else:
        message = 'N/A'

    newLogInfo = LogInfo(account_id=accountId,
                         log_date=datetime.now(
                             timezone.utc),
                         log_description=message)
    db.session.add(newLogInfo)
    db.session.commit()


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

        # X must only come from the physical keypad
        if actionValue == 'X':
            actionValue = 'Y'

        localBuf = KeypadHandler(actionValue)

    if localBuf[0:7] == 'Init - ':
        # initialize the user
        return redirect(url_for('pincode', mode=3, user=localBuf[7:]))

    return render_template('softkeypad.html', content=localBuf)


# entry point for the physical keypad
@app.route("/physicalkeypad", methods=['POST'])
def physicalkeypad():
    inputJson = request.get_json()
    actionValue = inputJson['keystroke']
    localBuf = KeypadHandler(actionValue)

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
    else:
        # extend session time
        session['adminMode'] = True

    typeMessage = 1
    message = None
    accountId = None
    if request.method == 'POST':
        # determine account
        accountId = request.form.get('account')

        actionValue = request.form.get('action')
        if actionValue == 'Reset':
            # reset account informations
            myData = db.session.get(Account, accountId)
            myData.email = None
            myData.password = None
            myData.initialized = False
            db.session.commit()

            # write to logInfo
            WriteLog(4, accountId)
        elif actionValue == 'Set':
            # get account informations
            myData = db.session.get(Account, accountId)

            # check the email
            email = request.form.get('mail')
            if email is None or email.strip() == '':
                message = 'E-Mail can\'t be empty...'
            elif myData.email is None or email.strip() != myData.email:
                if EmailExists(email):
                    message = 'E-Mail address already exists'
                else:
                    try:
                        email = validate_email(
                            email, check_deliverability=True).email

                        # set account informations
                        myData.email = email

                    except EmailNotValidError as e:
                        print(str(e))
                        message = 'E-Mail address not valid'

            if message is None:
                # generate a random password and convert string to byte
                pwd = str(randint(1000, 9999))
                bytePwd = pwd.encode('utf-8')

                # generate a new salt
                mySalt = bcrypt.gensalt()

                # hash password and save the hash
                myData.password = bcrypt.hashpw(bytePwd, mySalt)
                myData.initialized = False
                db.session.commit()

                # send mail
                msg = Message('PI From GIO', sender=config(
                    'MAIL_ADDRESS'), recipients=[email])
                msg.body = 'Hello ' + email + ' your init password is: ' + pwd
                mail.send(msg)

                typeMessage = 2
                message = 'E-Mail has been sended'

                # write to logInfo
                WriteLog(5, accountId)

    # get all data for accountId
    accountId = 'A' if accountId is None else accountId
    myData = db.session.query(Account).filter(Account.account_id == accountId)
    return render_template('accounts.html', accounts=myData, message=message, typeMsg=typeMessage)


@app.route("/onoff", methods=['GET', 'POST'])
def onoff():
    if request.method == 'POST':
        if request.form.get('action') == 'ON':
            GPIO.output(constant.LOCK_PIN, GPIO.HIGH)
            GPIO.output(constant.ALERT_PIN, GPIO.HIGH)
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
    #   mode=3 --> 3 controls to change password for user X
    modeOfPinCode = request.args.get('mode')
    user = request.args.get('user')
    message = None

    if request.method == 'POST':
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
            if not user is None:
                currentPwd = request.form.get('CurrentPassword')
                newPwd = request.form.get('NewPassword')
                if currentPwd != '' and newPwd != '' and newPwd == request.form.get('ConfirmPassword'):
                    # read data of user account
                    myData = db.session.get(Account, user)

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

                        # write to logInfo
                        WriteLog(6, user)

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

    return render_template('pincode.html', mode=modeOfPinCode, user=user, controls=listOfControls, message=message)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=config('DEBUG', cast=bool))
