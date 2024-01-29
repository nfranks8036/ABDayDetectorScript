import requests
import traceback
import os
import sys
import math
import json
from datetime import datetime, timedelta, date, time

def cmd(command):
    if UserInterface.is_external():
        os.system(command)

class Constants:
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    RCPS_WEBSITE = "https://www.rcps.us"

class Log:
    log_history = []
    
    @staticmethod
    def text(string: str):
        print(string)
        Log.log_history.append(string)

    def get_log_history():
        return Log.log_history

class Updater:
    DOWNLOAD_URL = "https://update.ab.download.noahf.net/"
    CHECK_URL = "https://update.ab.check.noahf.net/"
    VERSION = "0.1"
    
    def __init__(self):
        try:
            Log.text("[  --------- BEGIN CHECK FOR UPDATES ---------  ]")
            Log.text("Initializing updater...")
            Log.text("Found environment: " + str({
                "downloadUrl": self.DOWNLOAD_URL,
                "checkUrl": self.CHECK_URL,
                "currentVersion": self.VERSION}))

            self.check = requests.get(self.CHECK_URL)
            # self.check_content = self.check.text
            self.check_content = "\n".join(open("version-history.json", "r").readlines())
            Log.text("Found " + str(len(self.check_content.split("\n"))) + " lines (" + self.check.url + ")")

            self.latest_data = json.loads(self.check_content)
            Log.text("Found latest data: " + str(self.latest_data))
            if self.latest_data["latest"] != self.VERSION:
                Log.text("** OUT OF DATE **")
                self.delta_version = 0

                for index, version_from_history in enumerate(self.latest_data["history"]):
                    if self.VERSION == version_from_history:
                        Log.text("(found old version match " + self.VERSION + " == " + version_from_history + ", at index = " + str(index) + ")")
                        self.delta_version = index + 1
                        break

                Log.text("by " + str(self.delta_version) + " versions")

            Log.text("[  --------- END CHECK FOR UPDATES ---------  ]")
        except Exception as err:
            self.error = err
            Log.text(traceback.format_exc().strip())
            Log.text("Fatal exception (check for updates)")
            Log.text("Found exception " + str(type(err)) + ": " + str(err))
            Log.text("**********************************")
            Log.text("** FAILED TO CHECK FOR UPDATES! **")
            Log.text("**     SEE EXCEPTION ABOVE      **")
            Log.text("**    PLEASE CONTACT NOAH F:    **")
            Log.text("**        www.noahf.net         **")
            Log.text("**********************************")

class DatesFinder:
    def __init__(self):
        Log.text("[  --------- BEGIN DATES SRC FINDER ---------  ]")
        Log.text("Searching with base url '" + Constants.RCPS_WEBSITE + "'")
        self.url = None
        self.content = requests.get(Constants.RCPS_WEBSITE).text
        Log.text("Found " + str(len(self.content.split("\n"))) + " lines (" + Constants.RCPS_WEBSITE + ")")

        for index, line in enumerate(self.content.split("\n")):
            if not "/cms/lib/" in line:
                continue
            if not "aDayBDay_Dates" in line:
                Log.text("Invalid /cms/lib line found: (" + str(index) + ") " + line + " (FAILED TO FIND aDayBDay_Dates)")
                continue
            Log.text("Valid /cms/lib line found: (" + str(index) + ") " + line)
            begin_index = line.index('src="')
            Log.text("Begin index of 'src=' at " + str(begin_index))
            line = line[begin_index:len(line)]
            Log.text("Found URI of file to be at (excluding domain): " + str(line.split('"')[1]))
            self.url = Constants.RCPS_WEBSITE + line.split('"')[1]
            Log.text("New URL set to '" + self.url + "' (line #" + str(index) + ")")
            break

        Log.text("[  --------- END DATES SRC FINDER ---------  ]")

    def get_url(self):
        return self.url

class RCPSWebsiteReader:
    def date_from_text(self, text):
        return datetime.strptime(text, '%B %d, %Y %H:%M:%S').date()
    
    def __init__(self):
        Log.text("----------- BEGIN WEBSITE READER -----------")
        
        #self.url = "https://www.rcps.us/cms/lib/VA01818713/Centricity/Template/17/setup/aDayBDay_Dates-011624.js?v=011624"

        try:
            self.url = DatesFinder().get_url()
            Log.text("Website reader found neat URL: " + str(self.url))
            if self.url == None:
                raise RuntimeError("URL not defined nor found on RCPS website")
            
            self.content = requests.get(self.url).text
            Log.text("Found " + str(len(self.content.split("\n"))) + " lines")

            reading_days_off = False
            self.days_off = {}
            self.year_start = None
            self.year_end = None
            Log.text("** Inspected lines will be cherry-picked via if they match conditions **")
            for line in self.content.split("\n"):
                if "ListOfDaysOff =" in line:
                    reading_days_off = True
                    Log.text("---[ Now reading days off and their reason ]---")
                    continue

                if "StartOfYearDate =" in line:
                    Log.text("Inspecting: " + str(line))
                    self.year_start = self.date_from_text(line.split('"')[1])
                    Log.text("The year starts " + str(self.year_start))

                if "LastDayOfExams =" in line:
                    Log.text("Inspecting: " + str(line))
                    self.year_end = self.date_from_text(line.split('"')[1])
                    Log.text("The year ends " + str(self.year_end))

                if reading_days_off == True:
                    if "]" in line:
                        Log.text("Inspecting: " + str(line))
                        Log.text("Discovered NO LONGER reading days off, removing var")
                        reading_days_off = False
                        Log.text("Days off: " + str(self.days_off))
                        Log.text("---[ Exiting days off and their reason ]---")
                        continue


                    line = line.strip()
                    Log.text("Inspecting: " + line)
                    elements = line.split('\"')
                    if not len(elements) == 5:
                        Log.text("List element does not split properly, ignoring this element.")
                        continue
                        
                    date = elements[1]
                    reason = elements[3]

                    valid = False
                    for month in Constants.MONTHS:
                        if month in date:
                            valid = True
                            break
                    if valid == False:
                        Log.text("Failed to find month in list element, ignoring this element.")
                        continue

                    self.days_off[self.date_from_text(date)] = str(reason)
        except Exception as err:
             Log.text(traceback.format_exc())

        Log.text("----------- END WEBSITE READER -----------")
        Log.text(" ")

    def get_days_off(self):
        return self.days_off

    def get_year_start(self):
        return self.year_start

    def get_year_end(self):
        return self.year_end

class DayLetter:
    A_DAY = True
    B_DAY = False

    @staticmethod
    def value_of(boolean_type: bool):
        if boolean_type == True:
            return "A_DAY"
        elif boolean_type == False:
            return "B_DAY"
        return None

    @staticmethod
    def format(boolean_type: bool):
        if boolean_type == True:
            return "an A Day"
        elif boolean_type == False:
            return "a B Day"
        return None

class DateType:
    SCHOOL_DAY = 0
    SUMMER = 1
    WEEKEND = 2
    DAY_OFF = 3
    EXAM_DAY = 4

    @staticmethod
    def value_of(integer_type: int):
        if integer_type == 0:
            return "SCHOOL_DAY"
        elif integer_type == 1:
            return "SUMMER"
        elif integer_type == 2:
            return "WEEKEND"
        elif integer_type == 3:
            return "DAY_OFF"
        elif integer_type == 4:
            return "EXAM_DAY"
        return None

    @staticmethod
    def format(integer_type: int):
        if integer_type == 0:
            return "a school Day"
        elif integer_type == 1:
            return "a day in summer"
        elif integer_type == 2:
            return "a weekend"
        elif integer_type == 3:
            return "a day off"
        elif integer_type == 4:
            return "an exam day"
        return None

class ABDateAssigner:
    def get_ordinal_ending(self, cardinal):
        return "th" if 11 <= cardinal <= 13 else ("th" if cardinal % 10 > 3 else (["th", "st", "nd", "rd", "th"][cardinal % 10]))

    def normalize(self, unknown_datetime_object):
        obj = unknown_datetime_object
        if isinstance(obj, datetime):
            obj = obj.date()
        return obj
    
    def get_date_type(self, date):
        date = self.normalize(date)
        
        value = DateType.SCHOOL_DAY
        if as_epoch(date) < as_epoch(self.year_start) or as_epoch(date) > as_epoch(self.year_end):
            value = DateType.SUMMER
        elif date.weekday() == 5 or date.weekday() == 6:
            value = DateType.WEEKEND
        elif date in self.days_off.keys():
            value = DateType.DAY_OFF
        
        return value

    def get_day_letter(self, date):
        date = self.normalize(date)

        if not self.get_date_type(date) == DateType.SCHOOL_DAY:
            return None

        current_date = self.year_start
        day_letter = False                  # true = A day
        while as_epoch(current_date) < as_epoch(date + timedelta(days=1)):
            if self.get_date_type(current_date) == DateType.SCHOOL_DAY:
                day_letter = not day_letter
            current_date = current_date + timedelta(days=1)

        return day_letter
        

    def get_day_off_reason(self, date):
        date = self.normalize(date)

        if not self.get_date_type(date) == DateType.DAY_OFF:
            return None

        return self.days_off[date]
    
    def __init__(self, website: RCPSWebsiteReader):
        # self.today = datetime.now()
        Log.text("* Summary of Found Data *")
        
        self.today = datetime.now()
        Log.text("Today is " + str(self.today))

        self.year_start = website.get_year_start()
        self.year_end = website.get_year_end()

        Log.text("The year starts " + str(self.year_start))
        Log.text("The year ends " + str(self.year_end))

        self.days_off = website.get_days_off()
        Log.text("Found " + str(len(self.days_off.keys())) + " days off")

def as_epoch(date: datetime.date):
    if date == None:
        return None

    # month, day, and year DO NOT matter here because we're just getting the time in the end
    time = datetime(year=1, month=1, day=1, hour=12, minute=0, second=0).time()
    
    return round(datetime.combine(date, time).timestamp())

class Commands:
    def register(self, data: dict, function):
        self.commands[data["name"]] = {
            "data": data,
            "func": function
            }
        print("Registered command: " + str(data))

    def evaluate(self, inputted) -> bool:
        inputted_command = inputted.split(" ")[0]

        inputted_args = inputted.split(" ")
        inputted_args.pop(0)

        command = None
        for key in self.commands:
            command_info = self.commands[key]
            if key.lower() == inputted_command.lower():
                command = command_info
                break
            if key.lower() in command_info["data"]["aliases"]:
                command = command_info
                break
        return command["func"](inputted_args) if command is not None else False

    def __init__(self):
        self.commands = {}

        self.register(
            {"name": "logs",
             "aliases": ["showlogs", "log"]},
            self.logs
        )

    def logs(self, args):
        printF(" ")
        printF("&6LOG HISTORY:")
        for index, line in enumerate(Log.get_log_history()):
            printF(f"&c[&e{str(index + 1)}&c] &7" + str(line))
        printF(" ")
        return True

    def show_days_off(self, args):
        printF(" ")
        printF("&6DAYS OFF:")

class UserInterface:
    SEPARATORS = ["-", "->", "/", "//", "|"]
    
    def is_external(): # detects if the user is running in IDLE or not (used for color support and whatnot)
        return False if 'idlelib.run' in sys.modules else True

    def color(string, keycode, color):
        string = string.replace(keycode, color if UserInterface.is_external() ==  True else "")
        return string

    def color_full(string):
        string = UserInterface.color(string, "&0", "\u001b[30m")
        string = UserInterface.color(string, "&1", "\u001b[34m")
        string = UserInterface.color(string, "&2", "\u001b[32m")
        string = UserInterface.color(string, "&3", "\u001b[36m")
        string = UserInterface.color(string, "&4", "\u001b[31m")
        string = UserInterface.color(string, "&5", "\u001b[35m")
        string = UserInterface.color(string, "&6", "\u001b[33m")
        string = UserInterface.color(string, "&7", "\u001b[37m")
        string = UserInterface.color(string, "&8", "\u001b[30;1m")
        string = UserInterface.color(string, "&9", "\u001b[34;1m")
        string = UserInterface.color(string, "&a", "\u001b[32;1m")
        string = UserInterface.color(string, "&b", "\u001b[36;1m")
        string = UserInterface.color(string, "&c", "\u001b[31;1m")
        string = UserInterface.color(string, "&d", "\u001b[35;1m")
        string = UserInterface.color(string, "&e", "\u001b[33;1m")
        string = UserInterface.color(string, "&f", "\u001b[37;1m")
        string = UserInterface.color(string, "&l", "\u001b[1m")
        string = UserInterface.color(string, "&n", "\u001b[4m")
        string = UserInterface.color(string, "&h", "\u001b[7m")
        string = UserInterface.color(string, "&r", "\u001b[0m")
        string = UserInterface.color(string, "&o", "\u001b[3m")
        return string

    global printF
    def printF(string):
        print(UserInterface.color_full(string + "&r"))
    
    def __init__(self, ab_date_assigner: ABDateAssigner, commands: Commands):
        self.assigner = ab_date_assigner
        self.commands = commands

        Log.text("Clearing console, as it's no longer needed for debugging purposes...")
        Log.text(" ")
        Log.text(" ")
        Log.text(" ")
        Log.text(" ")

        cmd("cls")
        printF("&6SCHOOL DAY DETECTOR")
        printF("Welcome to the the school day detector.")
        printF(" ")
        printF("&6WHAT?")
        printF("This program lets you figure out if a day is going to be an A day or a B day.")
        printF("It also lets you figure out WHY a day is off.")
        printF(" ")
        printF("&6HOW?")
        printF("Enter a date below and the program will give you all information about it.")
        printF("The format should be: &aMONTH DAY YEAR")
        printF("For example: &e" + datetime.now().strftime("%B %d %Y"))
        printF(" ")
        self.ask_input()

    def error(self, msg, err):
        printF(" ")
        printF(" ")
        printF("&cAN ERROR OCCURRED!")
        if not err == None:
            printF("&cWe found this error to be the possible culprit: &8" + str(err))
            printF("&c&oIt's possible this is not your fault!")
            printF("&cSupplementary Message: &8" + msg)
        else:
            printF("&c&oWe found this message relating to your error:")
            printF(str(msg))
        printF(" ")

        self.ask_input()


    # LEGAL INPUTS:
    # Jan 17, 2024
    # Jan 17-18, 2024
    # Jan 17, 2024 - Jan 18, 2024
    # Jan 17, 2024-Jan 18, 2024

    def parse(self, user_input, format_type):
        tokens = user_input.split(" ")
        if len(tokens) == 3:
            month = tokens[0]
            year = tokens[2]
            returned = []
            for separator in UserInterface.SEPARATORS:
                dates = tokens[1].split(separator)
                if not len(dates) == 2:
                    continue
                minimum = min(int(dates[0]), int(dates[1]))
                maximum = max(int(dates[0]), int(dates[1]))

                for i in range(minimum, maximum+1):
                    returned.append(datetime.strptime(f"{month} {str(i)} {year}", format_type))

            if len(returned) != 0:
                return returned

                
                
        return datetime.strptime(user_input, format_type)

    def try_input(self, previous_date, user_input, format_type):
        if not isinstance(previous_date, Exception) and not isinstance(previous_date, list) and previous_date != None:
            return previous_date
        
        try:
            new_date = None
            if not isinstance(previous_date, list) and True == False:
                new_date = []
                for separator in UserInterface.SEPARATORS:
                    if not separator in str(user_input):
                        continue

                    split_at_space = user_input.split(" ")
                    if len(split_at_space) < 4:
                        continue

                    split_at_separator = user_input.split(separator)
                    for item in split_at_separator:
                        new_date.append(item)
            
            if isinstance(previous_date, list) or not new_date == None:
                new_list = []
                for date in previous_date if new_date == None else new_date:
                    if isinstance(date, str):
                        try:
                            date = self.parse(user_input, format_type)
                        except Exception as err:
                            pass # ignore because we'll just re-set it to a string

                    if isinstance(date, list):
                        for item in date:
                            new_list.append(item)
                    else:
                        new_list.append(date)

                return new_list

            return self.parse(user_input, format_type)
        except Exception as err:
            return err

    def ask_input(self, forced: str=None):
        inputted = input(UserInterface.color_full("Enter date or command: &b")) if forced == None else forced
        for ordinal in ["st", "nd", "rd", "th"]:
            inputted = inputted.replace(ordinal, "")

        if self.commands.evaluate(inputted.strip()):
            self.ask_input()
            return

        date = self.try_input(None, inputted, "%B %d %Y")
        date = self.try_input(date, inputted, "%b %d %Y")
        date = self.try_input(date, inputted, "%B %d, %Y")
        date = self.try_input(date, inputted, "%b %d, %Y")

        if isinstance(date, Exception) or date == None:
            self.error("Standard error of type " + str(type(date)), date)
            return

        printF(" ")
        printF(" ")
        if isinstance(date, list):
            for item in date:
                self.print_information(item, True)
            printF(" ")
        else:
            self.print_information(date)

        self.ask_input()

    def provide_information(self, date):
        date_type = self.assigner.get_date_type(date)
        day_letter = self.assigner.get_day_letter(date)
        day_off_reason = self.assigner.get_day_off_reason(date)
        
        prefix = ("That day is " if isinstance(date, list) == False else "")
        
        if not day_letter == None:
            return prefix + ("&c" if day_letter == DayLetter.A_DAY else "&9") + DayLetter.format(day_letter)
        elif not day_off_reason == None:
            return prefix + "&e" + day_off_reason
        else:
            return prefix + "&2" + DateType.format(date_type)
        raise RuntimeError("Information was not handled nor provided correctly to self.provide_information")

    def print_information(self, inputted_date, list_element=False):
        if not isinstance(inputted_date, list):
            inputted_date = [inputted_date] # format as list

        items = []
        for date in inputted_date:
            if not isinstance(date, type(datetime.today())):
                items.append(["&cInvalid date detected: ", "&8" + str(date)])
                continue
            items.append(
                [("&6&n" + Constants.MONTHS[date.month - 1].upper() + " " + str(date.day) + self.assigner.get_ordinal_ending(date.day).upper() + ", " + str(date.year)),
                (self.provide_information(date)),
                 " "]
            )

        for item in items:
            if list_element == True:
                printF("&r ".join(item))
                continue
            
            for date in item:
                printF(date)

if __name__ == "__main__":
    Log.text("Loading program...")
    try:
        Log.text("Date and time: " + str(datetime.now()))
        Log.text("Is non-IDLE? " + str(UserInterface.is_external()))
        Log.text("Loading color and title...")
        cmd("color")
        cmd("title School Day Detector - Retrieving Data...")

        Log.text("Still in __name__ (" + str(__name__) + "), instantiating valued classes...")
        updater = Updater()
        reader = RCPSWebsiteReader()
        assigner = ABDateAssigner(reader)
        commands = Commands()

        cmd("title School Day Detector")
        
        Log.text("Enjoy the program, made with <3 by Noah Franks")
        Log.text("| -> MAIN WEBSITE: www.noahf.net")
        Log.text("| -> WEBSITE COUNTERPART: www.noahf.net/school/days")
        Log.text("| -> LET'S GO TERRIERS!")
        Log.text("| -> CREATED IN JAN 2024")

        Log.text("Instantiating UserInterface...")

        ui = UserInterface(assigner, commands)
    except Exception as err:
        print("A fatal exception has occurred. The program will exit momentary.")
        print("Found error that may be related: " + str(err))

    cmd("pause >NUL")

    #test_day = datetime(month=1, day=17, year=2024)
    
    #print("DATE TYPE: " + str(DateType.value_of(assigner.get_date_type(test_day))))
    #print("DAY OFF REASON: " + str(assigner.get_day_off_reason(test_day)))
    #print("DAY LETTER: " + str(DayLetter.value_of(assigner.get_day_letter(test_day))))
