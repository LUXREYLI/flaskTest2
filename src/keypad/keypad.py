import RPi.GPIO as GPIO


class keypad():
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # CONSTANTS
        self.KEYPAD = [
            ["1", "2", "3", "A"],
            ["4", "5", "6", "B"],
            ["7", "8", "9", "C"],
            ["*", "0", "#", "D"]
        ]

        self.isKeyPressed = False

        self.ROW = [5, 6, 13, 19]
        self.COLUMN = [12, 16, 20, 21]

        # Set all rows as output
        for j in range(len(self.ROW)):
            GPIO.setup(self.ROW[j], GPIO.OUT)

        # Set all columns as input
        for i in range(len(self.COLUMN)):
            GPIO.setup(self.COLUMN[i], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def getKey(self):
        while True:
            # Scan rows/columns for pushed key/button
            # A valid key press should set "colVal" between 0 and 3.
            rowVal = -1
            colVal = -1

            for i in range(len(self.ROW)):
                GPIO.output(self.ROW[i], GPIO.HIGH)
                for j in range(len(self.COLUMN)):
                    tmpRead = GPIO.input(self.COLUMN[j])
                    if tmpRead == 1:
                        rowVal = i
                        colVal = j
                GPIO.output(self.ROW[i], GPIO.LOW)

            if 0 <= colVal <= 3 and not self.isKeyPressed:
                # colVal is between 0 and 3 then button was pressed and we can exit
                self.isKeyPressed = True
                break
            elif colVal < 0 and self.isKeyPressed:
                # no key is pressed
                self.isKeyPressed = False

        # Return the value of the key pressed
        return self.KEYPAD[rowVal][colVal]
