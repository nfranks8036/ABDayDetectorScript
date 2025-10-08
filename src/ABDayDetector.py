from tqdm import tqdm
from datetime import datetime, timedelta, date, time
from collections import OrderedDict
import requests
import traceback
import os
import sys
import math
import json
import subprocess
import re
import platform
import time as threadcontrol

def cmd(command):
    # if we're using IDLE to see sys.out, then we probably don't want to execute commands
    # (opening commands in IDLE just opens a cmd.exe window for a few seconds, which is pointless as it
    #  doesn't affect the IDLE window)
    # (external here counts as not in the python idle window)
    if UserInterface.is_external():
        os.system(command)

class Constants:
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    RCPS_WEBSITE = "https://www.rcps.us"
    GITHUB_LINK = "github.com/nfranks8036/ABDayDetectorScript/releases"

# Log.text(str) is a replacement of print() when the program is starting so the history
# can be saved and viewed later via the command "logs"
# (that is seriously the only reason this exists)
class Log:
    log_history = []
    
    @staticmethod
    def text(string: str):
        if "--line-log" not in sys.argv and not (len(sys.argv) > 1 and "--minimal" in sys.argv):
            print(string)

        if len(sys.argv) > 1 and "--line-log" in sys.argv:
            columns = os.get_terminal_size()[0]
            print(string[0:(columns - 5)] + (" " * (columns - len(string))), end="\r")
        Log.log_history.append(string)

    def get_log_history():
        return Log.log_history

# Updates the program when it becomes out of date
class Updater:

    # this is the version the program thinks it is, please do not change
    VERSION = "1.8.2"

    DOWNLOAD_URL = "https://update.ab.download.noahf.net/"
    CHECK_URL = "https://update.ab.check.noahf.net/"
    FOLDER = "https://raw.githubusercontent.com/nfranks8036/ABDayDetectorScript/main/src/"
    DEV_BUILD = False # True will prevent users from downloading this file or you from uploading it

    BLOCK_SIZE = 1024

    # download a specified URL
    # the "path" is where the file is going to be saved to in the current working directory (CWD)
    def download(self, url, path):
        def name_from_path(path):
            split_items = path.split("\\")
            return split_items[len(split_items) - 1]
        
        Log.text("-> Downloading '" + str(url) + "'")
        if self.DEV_BUILD == True:
            # do NOT download dev builds, they were likely uploaded by accident
            raise ValueError("Download refused by client, is dev build? " + str(self.DEV_BUILD).upper())
        request = requests.get(url, stream=True) #stream required for future "tqdm"
        #file_size = int(request.headers.get('Content-Length', 0))
        file_size = len(request.content)
        all_data = []
        with tqdm( # tqdm for progress bar and data delay
            desc=name_from_path(path),
            total=file_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            for data in request.iter_content(chunk_size=1024):
                # if the version is not what it says it is, then we should not install this version
                # it is likely that github hasn't updated githubusercontent.com yet for this file, even though
                # version-history.json is up-to-date
                # This problem in the way it was described is usually solved within 12 hours or less
                if 'VERSION = \"' in str(data) and not ("VERSION = \"" + str(self.latest_version) + "\"" in str(data)):
                    Log.text("Uh oh! Cannot find 'VERSION = \"" + str(self.latest_version) + "\"' in data ('" + str(data) + "')")
                    raise RuntimeError("Download refused by safety mechanism, found possibly outdated version (GitHub not updating raw.githubusercontent.com?). This may warrant the user to contact Noah at www.noahf.net")

                # separated into numerous strings as to not trip the system itself lol
                if "DEV_BUILD " + "=" + " True" in str(data):
                    raise RuntimeError("Download refused by safety mechanism, found possible dev build download.\n\n" + ("*" * 60) + "\n IF YOU SEE THIS, PLEASE CONTACT NOAH AT www.noahf.net \n" + ("*" * 60) + "\n\n")
                all_data.append(data)
                bar.update(len(data))

        # we download the data first, then place it in a file in case the download fails at any point
        # we do not want a half-written file because the internet connection stopped midway through download
        # this is how Google Play Store and Apple App Store work with "Downloading" and then "Installing"
        with open(path, "wb") as file:
            for datum in all_data:
                file.write(datum)

        # bar.n is ultimately how much data was downloaded, so we can compare this to what the file size
        # should be to determine if it all successfully downloaded, += 100 bytes (hence the "file_size / 100")
        if file_size != 0 and round(bar.n / 100) != round(file_size / 100):
            raise RuntimeError("Failed to download file from url '" + str(url) + "'")

        Log.text("<- Downloaded '" + str(url) + "'")
        Log.text(" ")

    # starting the downloda does not necessarily mean this function downloads the data but rather
    # starts the child downloads of the files. see Updater.download for the function that downloads
    def start_download(self):
        self.download_error = None
        Log.text("[  --------- BEGIN UPDATE DOWNLOADER ---------  ]")
        try:
            try:
                Log.text("Sending request for data to " + str(self.DOWNLOAD_URL) + "...")
                request = requests.get(self.DOWNLOAD_URL)
                Log.text("Received response from " + str(request.url) + "!")
                request = request.text
                Log.text("Received " + str(len(request.split("\n"))) + " line(s) of data")
                json_data = json.loads(request)
            except Exception as err:
                # the school blocks api.github.com on school computers, thus this would fail every time if
                # this was not a check. githubusercontent is not blocked and thus we will ignorantly use that
                Log.text("Failed to get from " + self.DOWNLOAD_URL + ", ignorantly assuming file and folder")
                Log.text("(This sometimes happens because the school blocked 'api.github.com')")
                json_data = {
                    "tree": [
                            {"path": "ABDayDetector.py"}
                        ]
                    }

            Log.text("Folder of all files set to " + str(self.FOLDER) + ", looking to download " + str(len(json_data["tree"])) + " file(s)")

            Log.text("Executing ~" + str(len(json_data["tree"])) + " download(s)...")
            Log.text(" ")
            tree = json_data["tree"]
            file_urls = []
            for file in tree:
                self.download(self.FOLDER + str(file["path"]), __file__)
        except KeyboardInterrupt as err:
            Log.text("[  ---------       (MANUAL)        ---------  ]")
            Log.text("[  --------- END CHECK FOR UPDATES ---------  ]")
            raise err
        except Exception as err:
            Log.text(traceback.format_exc().strip())
            Log.text("DOWNLOADER FAILED: " + str(type(err)) + " " + str(err))
            self.download_error = err
        Log.text("[  --------- END CHECK FOR UPDATES ---------  ]")
        Log.text(" ")
    
    # forces the program to error out to test development tools related to it
    # different numbers mean different locations for the error to occur
    # can also be activated by the sys arg flag --force-error <num>
    # None = no force error happening this boot
    # 0 = before the FindDatesList attempts to pull from the website
    # 1 = while the FindDatesList is iterating through lines
    # 2 = after the FindDatesList finishes its duty
    # 3 = when RCPSWebsiteReader starts
    # 4 = before RCPSWebsiteReader inspects the detected lines
    # 5 = while RCPSWebsiteReader is inspecting the detected lines
    # 6 = after RCPSWebsiteReader has completed its duties
    # 7 = while ABDayAssigner attempts to normalize all the detected days off
    # 8 = whenever anybody tries to grab the year start from RCPSWebsiteReader
    # 9 = whenever anybody tries to grab the year end from RCPSWebsiteReader
    FORCE_ERROR_LOCATIONS = {
            None: "no force error happening this boot",
            0: "before the FindDatesList attempts to pull from the website",
            1: "while the FindDatesList is iterating through lines",
            2: "after the FindDatesList finishes its duty",
            3: "when RCPSWebsiteReader starts",
            4: "before RCPSWebsiteReader inspects the detected lines",
            5: "while RCPSWebsiteReader is inspecting the detected lines",
            6: "after RCPSWebsiteReader has completed its duties",
            7: "while ABDayAssigner attempts to normalize all the detected days off",
            8: "whenever anybody tries to grab the year start from RCPSWebsiteReader",
            9: "whenever anybody tries to grab the year end from RCPSWebsiteReader",
        }
    FORCE_ERROR = None
    
    @staticmethod
    def check_force_error(position):
        if Updater.FORCE_ERROR == None:
            return
        elif not Updater.FORCE_ERROR == position:
            return
        Log.text(f"#################### FORCE ERROR APPLIED AT THIS POSITION ({str(position)}) ####################")
        raise Exception(f"Force error activated at position {str(position)}")
    
    def __init__(self):
        Log.text("[  --------- BEGIN CHECK FOR UPDATES ---------  ]")
        try:
            self.force_latest = None
            if len(sys.argv) > 1:
                Log.text("FOUND SYSTEM ARGUMENTS: " + str(sys.argv))
                for index, arg in enumerate(sys.argv):
                    if sys.argv[index - 1] == "--version":
                        Updater.VERSION = arg
                    elif sys.argv[index - 1] == "--latest":
                        self.force_latest = arg
                    elif sys.argv[index - 1] == "--dev-build":
                        Updater.DEV_BUILD = bool(arg)
                    elif sys.argv[index - 1] == "--force-error":
                        try:
                            Updater.FORCE_ERROR = int(arg)
                        except ValueError:
                            Updater.FORCE_ERROR = None

            Log.text("Initializing updater...")
            Log.text("Found environment: " + str({
                "downloadUrl": self.DOWNLOAD_URL,
                "checkUrl": self.CHECK_URL,
                "currentVersion": self.VERSION}
            ))

            # delta_version = 0 means the program is up-to-date
            # delta_version > 0 means the program is out-of-date by x versions
            # delta_version = -1 means the program can't find how far out-of-date it is (could be a dev build)
            self.delta_version = 0

            check = requests.get(self.CHECK_URL)
            check_content = check.text
            Log.text("Found " + str(len(check_content.split("\n"))) + " lines (" + check.url + ")")

            latest_data = json.loads(check_content)

            if self.force_latest is not None:
                latest_data["latest"] = self.force_latest

            self.latest_version = latest_data["latest"]
            self.latest_history = latest_data["history"]
            Log.text("Found latest data: " + str(latest_data))
            if not latest_data["latest"] == self.VERSION:
                Log.text("** OUT OF DATE **")
                self.delta_version = -1

                for index, version_from_history in enumerate(latest_data["history"]):
                    if self.VERSION == version_from_history:
                        Log.text("(found old version match " + self.VERSION + " == " + version_from_history + ", at index = " + str(index) + ")")
                        self.delta_version = index + 1
                        break

                Log.text("by " + str(self.delta_version) + " versions")

            if self.delta_version == -1:
                Log.text("Final call: OUT OF DATE?")  
            elif self.delta_version == 0:
                Log.text("Final call: ZERO VERSIONS BEHIND!")
            elif self.delta_version > 0:
                Log.text(f"Final call: {str(self.delta_version)} versions behind")

        except requests.exceptions.ConnectionError as err:
            Log.text(traceback.format_exc().strip())
            Log.text(" ")
            Log.text(" ")
            Log.text(" ")
            Log.text("*************************************************************************")
            Log.text("**            Failed to retrieve data from the internet.               **")
            Log.text("**                Are you connected to the internet?                   **")
            Log.text("** You must be connected to the internet in order to use this program! **")
            Log.text("**                                                                     **")
            Log.text("**                     (press enter to exit)                           **")
            Log.text("*************************************************************************")
            os.system("pause >NUL")
            exit()
        except Exception as err:
            self.error = err
            self.delta_version = -1
            Log.text(traceback.format_exc().strip())
            Log.text("Fatal exception (check for updates)")
            Log.text("Found exception " + str(type(err)) + ": " + str(err))
            Log.text("**********************************")
            Log.text("** FAILED TO CHECK FOR UPDATES! **")
            Log.text("**     SEE EXCEPTION ABOVE      **")
            Log.text("**    PLEASE CONTACT NOAH F:    **")
            Log.text("**        www.noahf.net         **")
            Log.text("**********************************")

        Log.text("[  --------- END CHECK FOR UPDATES ---------  ]")

class FindDatesList:
    def __init__(self):
        Log.text("[  --------- BEGIN FIND DATES LIST ---------  ]")

        Updater.check_force_error(0)
    
        url = Constants.RCPS_WEBSITE
        Log.text("RCPS Website: " + url)
        
        true_content = requests.get(url).text
        Log.text("Found " + str(len(true_content.split("\n"))) + " lines on the RCPS website!")

        self.content = []
        dates_script = False
        for line in true_content.split("\n"):
            Updater.check_force_error(1)
            
            if "The following four sections must be updated " in line:
                dates_script = True
                continue

            if not dates_script:
                continue

            if "Nothing should need to be updated below this line." in line:
                dates_script = False
                break

            self.content.append(line)

        Log.text("Filtered website to " + str(len(self.content)) + " lines!")

        Updater.check_force_error(2)

        Log.text("[  --------- END FIND DATES LIST ---------  ]")

    def get_content(self):
        return self.content


class RCPSWebsiteReader:
    def date_from_text(self, text):
        return datetime.strptime(text, '%B %d, %Y %H:%M:%S').date()
    
    def __init__(self):
        Log.text("----------- BEGIN WEBSITE READER -----------")
        
        Updater.check_force_error(3)
        
        #self.url = "https://www.rcps.us/cms/lib/VA01818713/Centricity/Template/17/setup/aDayBDay_Dates-011624.js?v=011624"

        self.content = FindDatesList().get_content()
            
        Updater.check_force_error(4)
        
        reading_days_off = False
        self.days_off = {}
        self.year_start = None
        self.year_end = None
        Log.text("** Inspected lines will be cherry-picked via if they match conditions **")
        for line in self.content:
            Updater.check_force_error(5)
            if "ListOfDaysOff =" in line:
                # we are now reading the days off and the program needs to know lmao
                reading_days_off = True
                Log.text("---[ Now reading days off and their reason ]---")
                continue

            if "StartOfYearDate =" in line: #StartOfYearDate =
                Log.text("Inspecting: " + str(line))
                self.year_start = self.date_from_text(line.split('"')[1])
                Log.text("The year starts " + str(self.year_start))

            if "LastDayOfExams =" in line:
                Log.text("Inspecting: " + str(line))
                self.year_end = self.date_from_text(line.split('"')[1])
                Log.text("The year ends " + str(self.year_end))

            if reading_days_off == True:
                if "]" in line:
                    # arrays in JS end in "]", we know we're done with days off now
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

                # lines often look like: new Date("August 1, 2023 12:00:00")
                # we can split at " and get first element ([0])
                    
                date = elements[1]
                reason = elements[3]

                # we need a way to verify the line, thus we use the month
                # the constants class contains every month that could possibly exist
                # and since the date will need a month (because, it's a *DATE*), this
                # becomes a reliable way to check for validity
                valid = False
                for month in Constants.MONTHS:
                    if month in date:
                        valid = True
                        break
                if valid == False:
                    Log.text("Failed to find month in list element, ignoring this element.")
                    continue

                try:
                    self.days_off[self.date_from_text(date)] = str(reason)
                except Exception as err:
                    Log.text("LINE FAILED TO TURN INTO DATE: " + line + ", CONSIDER INSPECTING!")
                    Log.text("^^^ ERROR: " + str(type(err)) + " - " + str(err))
             
        Updater.check_force_error(6)

        Log.text("----------- END WEBSITE READER -----------")
        Log.text(" ")

    def get_days_off(self):
        return self.days_off

    def get_year_start(self):
        Updater.check_force_error(8)
        return self.year_start

    def get_year_end(self):
        Updater.check_force_error(9)
        return self.year_end

class DayLetter:
    # A day is always true and B day is always false
    # this is also how the county calculates it in their own calculation
    
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
    OUT_OF_SCOPE = 1 # the county calls this "SUMMER" for some fricking reason
    WEEKEND = 2
    DAY_OFF = 3
    EXAM_DAY = 4 # not used in this program because I haven't seen it used since 2021, can't be bothered to implement tbh

    @staticmethod
    def value_of(integer_type: int):
        if integer_type == 0:
            return "SCHOOL_DAY"
        elif integer_type == 1:
            return "OUT_OF_SCOPE"
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
            return "not in this school year"
        elif integer_type == 2:
            return "a weekend"
        elif integer_type == 3:
            return "a day off"
        elif integer_type == 4:
            return "an exam day"
        return None

class ABDateAssigner:
    # ordinal number examples:
    # first (1st), second (2nd), third (3rd)
    # as opposed to cardinal:
    # one (1), two (2), three (3)
    def get_ordinal_ending(self, cardinal):
        return "th" if 11 <= cardinal <= 13 else ("th" if cardinal % 10 > 3 else (["th", "st", "nd", "rd", "th"][cardinal % 10]))

    # datetime has "date", "datetime", and "time" objects
    # we ONLY want date objects (time is unnecessary), so we normalize it into a "date" object
    def normalize(self, unknown_datetime_object):
        obj = unknown_datetime_object
        if isinstance(obj, datetime):
            obj = obj.date()
        return obj
    
    def get_date_type(self, date):
        date = self.normalize(date)
        
        value = DateType.SCHOOL_DAY
        if as_epoch(date) < as_epoch(self.year_start) or as_epoch(date) > as_epoch(self.year_end):
            # after a certain day in august and before a certain day in may
            value = DateType.OUT_OF_SCOPE
        elif date.weekday() == 5 or date.weekday() == 6:
            # weekday == 5 (saturday)
            # weekday == 6 (sunday)
            value = DateType.WEEKEND
        elif date in self.days_off.keys():
            value = DateType.DAY_OFF
        
        return value

    def get_every_day_information(self):
        days = {}
        
        school_days = {}
        calendar_days = 0
        amt_days_off = 0

        Updater.check_force_error(7)
        Log.text("|- Compiling date information from year_start...")
        current_date = self.year_start
        day_letter = False # true = A Day
        while as_epoch(current_date) < as_epoch(self.year_end + timedelta(days=1)):
            date_type = self.get_date_type(current_date)
            days[current_date] = {
                    "type": date_type,
                    "index": {
                        "calendar": calendar_days,
                        "school": school_days["ALL"] if "ALL" in school_days.keys() else 0
                    },
                    "_meta_": None
            }
            
            if date_type == DateType.SCHOOL_DAY:
                day_letter = not day_letter
                if not ("ALL" in school_days.keys()):
                    school_days["ALL"] = 0
                if not (DayLetter.value_of(day_letter) in school_days.keys()):
                    school_days[DayLetter.value_of(day_letter)] = 0
                
                school_days["ALL"] += 1
                school_days[DayLetter.value_of(day_letter)] += 1
                days[current_date]["_meta_"] = {
                    "day_letter_formatted": DayLetter.value_of(day_letter),
                    "day_letter": day_letter
                }
            elif date_type == DateType.DAY_OFF:
                days[current_date]["_meta_"] = {
                    "reason": self.get_day_off_reason(current_date)
                }
                amt_days_off += 1

            calendar_days += 1
            current_date = current_date + timedelta(days=1)

        days["_meta_"] = {
            "school_days": school_days,
            "calendar_days": calendar_days,
            "days_off": amt_days_off
        }
        Log.text("| Found " + str(calendar_days) + " calendary days")
        
        def stringify_dates(obj):
            if isinstance(obj, dict):
                return {stringify_dates(k): stringify_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [stringify_dates(i) for i in obj]
            elif isinstance(obj, date):
                return str(obj)
            else:
                return obj
        
        loc = os.getenv("TEMP")
        ab_day_detector_dir = os.path.join(loc, "ABDayDetector")
        os.makedirs(ab_day_detector_dir, exist_ok=True)
        days_file = os.path.join(ab_day_detector_dir, "cached_days.json")
        Log.text("| Creating cached days at " + days_file)
        
        f = open(days_file, "w")
        Log.text("| Writing (and stringifying) dictionary...")
        f.write(json.dumps(stringify_dates(days), indent=4))
        f.close()

        Log.text("|- Wrote File")

        return days
            

    def get_day_letter(self, date):
        date = self.normalize(date)

        if not self.get_date_type(date) == DateType.SCHOOL_DAY:
            return None

        # this is the same as going through every day since the beginning of the year and
        # counting "A" then "B" then "A" while skipping days off, breaks, and weekends accurately
        # (except this is much faster cuz hooman slow, compter fast)

        return self.days[date]["_meta_"]["day_letter"]

    def get_day_off_reason(self, date):
        date = self.normalize(date)

        if not self.get_date_type(date) == DateType.DAY_OFF:
            return None

        return self.days_off[date]

    def get_next_school_day(self, from_date):
        date = self.normalize(from_date)

        # thursday -> friday
        # friday -> monday
        # friday -> tuesday (if we have monday off)

        for index in range(0, 14):
            date = date + timedelta(days=1)
            if self.days[date]["type"] == DateType.SCHOOL_DAY:
                return date

        return None

    def get_progression(self, date):
        date = self.normalize(date)

        indices = self.days[date]["index"]
        return indices["calendar"], indices["school"]

    def get_total_days(self):
        return self.days["_meta_"]["calendar_days"], self.days["_meta_"]["school_days"]["ALL"]
    
    def __init__(self):
        self.fatal_error = None
        # self.today = datetime.now()
        
        try:
            website = RCPSWebsiteReader()
        except Exception as err:
            self.fatal_error = err
            self.fatal_traceback = err.__traceback__
            Log.text(f"FATAL ERROR in reading the RCPS website: {str(err)}")
            return
        
        Log.text("* Summary of Found Data *")
        
        self.today = datetime.now()
        Log.text("Today is " + str(self.today))

        try:
            self.year_start = website.get_year_start()
            self.year_end = website.get_year_end()

            Log.text("The year starts " + str(self.year_start))
            Log.text("The year ends " + str(self.year_end))
            
            if self.year_start == None or self.year_end == None:
                raise Exception("Either year start or year end is absent.")
        except Exception as err:
            self.fatal_error = err
            self.fatal_traceback = err.__traceback__
            Log.text(f"FATAL ERROR in finding year start and year end: {str(err)}")
            return

        try:
            self.days_off = website.get_days_off()
            Log.text("Found " + str(len(self.days_off.keys())) + " days off")
            
            if str(len(self.days_off.keys())) == 0:
                raise Exception("No days off detected: 0")
        except Exception as err:
            self.fatal_error = err
            self.fatal_traceback = err.__traceback__
            Log.text(f"FATAL ERROR in finding days off: {str(err)}")
            return

        try:
            self.days = self.get_every_day_information()
            Log.text("Found " + str(len(self.days) - 1) + " calendar days")
        except Exception as err:
            self.fatal_error = err
            self.fatal_traceback = err.__traceback__
            Log.text(f"FATAL ERROR in finding calendar days: {str(err)}")
            return

    def get_days_off(self):
        return self.days_off

# as epoch (or unix time) in seconds
def as_epoch(date: datetime.date):
    if date == None:
        return None

    # month, day, and year DO NOT matter here because we're just getting the time in the end
    # going with the counties reason as to why 12pm, +- an hour will not matter here for DST reasons
    time = datetime(year=1, month=1, day=1, hour=12, minute=0, second=0).time()
    
    return round(datetime.combine(date, time).timestamp())

def get_last_day_of_month(day):
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

# commands are the alternate to writing a date in the command line
# they execute arbitrary code with certain argumetns
class Commands:
    def register(self, data: dict, function, require=None):
        # structure:
        # {[
        #   "command_name": {
        #       "data": {
        #           "name": "command_name",
        #           "aliases": ["alias1", "alias2"]
        #       },
        #       "func": <internal function>
        #   }
        # ]}
        
        self.commands[data["name"]] = {
            "data": data,
            "func": function,
            "reqs": require,
            }
        Log.text("Registered command: " + str(data))

    def conditional_register(self, assigner):
        if assigner.fatal_error is not None:
            self.register(
                {"name": "inspect",
                 "aliases": ["showfatal"],
                 "desc": "Inspects a fatal error if they occur."},
                self.inspect,
                self.req_fatal_error
            )
        
        return self

    # evaluates a given input from the command line, usually barely touched by the program already
    def evaluate(self, ui, inputted) -> bool:
        # example input
        # command argument1 argument2 argument3
        
        inputted_command = inputted.split(" ")[0].lower()

        inputted_args = inputted.split(" ")
        inputted_args.pop(0)

        command = None
        for key in self.commands:
            command_info = self.commands[key]
            if inputted_command == key.lower(): # check if they executed command name
                command = command_info
                break
            if inputted_command in command_info["data"]["aliases"]: # check if they executed alias
                command = command_info
                break
        
        try:
            if command is not None and command["reqs"] is not None and command["reqs"](ui) == False:
                raise Exception("This command failed a required condition, no other information was specified.")
        except Exception as err:
            printF(" ")
            printF(f"&cFailed to execute {str(inputted_command)}, try again later!")
            printF(f"&7&o{str(err)}")
            printF(" ")
            return True
        
        return command["func"](ui, inputted_args) if command is not None else False

    def req_no_fatal_errors(self, ui):
        if ui.assigner.fatal_error is None:
            return True
        raise Exception("This command is disabled because a fatal exception in the program was detected. Try restarting your program by typing 'restart' and view the start message for more information.")

    def req_fatal_error(self, ui):
        if ui.assigner.fatal_error is not None:
            return True
        raise Exception("This command is disabled because no fatal errors have occurred!")

    # register all the commands because yes this is necessary and no I'm not doing the python
    # version of java reflections, this is easier for now
    def __init__(self):
        self.commands = {}

        self.register(
            {"name": "help",
             "aliases": ["?", "/help", "dateformats", "dateformat", "commands", "command", "cmd", "cmds", "formats", "format", "dates", "date"],
             "desc": "Displays this help menu"},
            self.help
        )
        self.register(
            {"name": "logs",
             "aliases": ["showlogs", "log"],
             "desc": "Shows any log messages that occurred when the program started."},
            self.logs
        )
        self.register(
            {"name": "version",
             "aliases": ["ver", "v"],
             "desc": "Checks the version of the program and how far behind it is."},
            self.version
        )
        self.register(
            {"name": "upgrade",
             "aliases": ["update", "improve", "updates", "upgrades"],
             "desc": "Upgrades the program to the latest version if applicable."},
            self.upgrade
        )
        self.register(
            {"name": "restart",
             "aliases": ["rs", "reboot", "rb"],
             "desc": "Closes and re-opens the program; performs a restart."},
            self.restart
        )
        self.register(
            {"name": "exit",
             "aliases": ["stop", "end"],
             "desc": "Closes the program window."},
            self.exit
        )
        self.register(
            {"name": "today",
             "aliases": [],
             "desc": "Checks the A or B day status of the current day."},
            self.today,
            
            self.req_no_fatal_errors
        )
        self.register(
            {"name": "showdays",
             "aliases": ["days", "day", "showdaysoff", "daysoff", "show_days_off", "showbreak", "showbreaks", "breaks", "break"],
             "desc": "Shows all days off and breaks, how many days are left for school, and how many days has it been."},
            self.show_days,
            
            self.req_no_fatal_errors
        )
        self.register(
            {"name": "share",
             "aliases": [],
             "desc": "Gives a link to share if you would like to distribute this program."},
            self.share
        )
        self.register(
            {"name": "contact",
             "aliases": ["contactme", "bug", "issue", "bugs", "issues", "needhelp"],
             "desc": "Shows you the contact information for Noah F. Use this if you need any help or find any issues."},
            self.contact
        )

    def help(self, ui, args):
        printF(" ")
        printF("&6AVAILABLE COMMANDS:")
        for key in self.commands:
            command = self.commands[key]
            enabled = True
            try:
                if command["reqs"] is not None and command["reqs"](ui) == False:
                    raise Exception()
            except Exception as err:
                enabled = False
            printF(("&b" if enabled == True else "&c") + str(command["data"]["name"]) + "&f: " + str(command["data"]["desc"]))
        printF(" ")
        if ui.assigner.fatal_error is None:
            printF("&6AVAILABLE DATE FORMATS:")
            for date_format in UserInterface.DATE_FORMATS:
                raw_format = date_format
                character_map = UserInterface.DATES_CHARACTER_MAP
                for key in character_map.keys():
                    date_format = date_format.replace(key, character_map[key][0])
                printF("&b" + str(date_format) + "&f: " + datetime.now().strftime(raw_format))
        else:
            printF("&6ERROR!")
            printF("&fIt seems a fatal error occurred while trying to grab and/or calculate the necessary information.")
            printF("&fUnfortunately, &cthis means the program cannot continue as intended.")
            printF("&fMost features have been disabled to prevent crashes.")
            printF("")
            printF("&r&6SOLUTIONS:")
            printF("&r&5| &fEnsure you are connected to a stable internet connection.")
            printF("&r&5| &fCheck if the program is outdated by typing &bversion&f.")
            printF("&r&5|     &7&o(If outdated, consider upgrading by typing &b&oupgrade&7&o)")
            printF("&r&5| &fReinstall the program by typing &bupgrade force&f, which can fix a lot of issues.")
            printF("&r&5| &fContact the developer for any other issues by typing &bcontact&f.")
            printF("")
            printF("&6DETECTED ERROR:")
            printF(f"&8&o{str(ui.assigner.fatal_error)}, see more with &b&oinspect")
        printF(" ")
        return True

    def contact(self, ui, args):
        printF(" ")
        printF("&6WEBSITE: &bwww.noahf.net")
        printF("&6INSTAGRAM: &bwww.instagram.com/noahf8036")
        printF("&6TWITTER (X): &bwww.x.com/noahf8036")
        printF("&6EMAIL: &bnfranks8036@gmail.com")
        printF(" ")
        return True

    def restart(self, ui, args):
        printF(" ")
        internal, refresh = False, False
        for index, arg in enumerate(args):
            if "--internal" in arg:
                internal = True
            if "--refresh" in arg or "-rf" in arg:
                refresh = True
                args.append("--internal")
                args.append("--minimal")
                args.append("--line-log")
            if "-fe" in arg:
                args[index] = "--force-error"

        if refresh == False:
            printF(" ")
            printF("&2Restarting script, please wait...")
        elif refresh == True:
            printF("&2Refreshing script, please wait...")

        if internal == True and not "--minimal" in args:
            os.system("cls")
        subprocess.Popen([sys.executable, str(__file__)] + args, creationflags=subprocess.CREATE_NEW_CONSOLE if internal == False else 0)
        exit()
        printF("&7&oYou may close this terminal window.")
        return True
    
    def exit(self, ui, args):
        printF(" ")
        printF(" ")
        printF("&cExiting script, please wait...")
        exit()
        printF("&7&oYou may close this terminal window.")
        return True

    def upgrade(self, ui, args):
        printF(" ")
        if ui.updater.delta_version == 0 and not (len(args) == 1 and "force" in args[0]):
            printF("&aYou are using the latest version. =D")
            printF(f'&7&oIf this is a mistake, you can force an update by typing "&bupgrade force&r&7&o" &8(this is generally not advised)')
            printF(" ")
            return True
        elif ui.updater.delta_version == -1 and (len(args) == 1 and "confirm" in args[0]):
            printF("&cWe failed to detect if you are behind in version.")
            printF('&eTo confirm you would like to upgrade, type "&bupgrade confirm&e"')
            printF("&eThere is not necessarily any risk to upgrading unless you tinkered with the program.")
            printF("&eIf you tinkered with it, it could override any changes you made.")
            printF("&bContact Noah if any issuess arise, see contacts at &9www.noahf.net")
            return True

        try:
            printF("&7&oStarting upgrade processs...")
            printF("&7&oPress 'CTRL' + 'C' if you wish to cancel.")
            printF(" ")
            threadcontrol.sleep(3) # time.sleep(3)
            ui.updater.start_download()

            if ui.updater.download_error is not None:
                raise ui.updater.download_error

            printF("&aUpdate successful!")
            printF("&fYou &cMUST &frestart the script to see changes.")
            printF("&fType \"&brestart&f\" in the console window.")
            printF(" ")
        except KeyboardInterrupt as keyboard:
            printF("&cYou cancelled the update!")
            printF(" ")
        except Exception as err:
            printF("&cFailed to upgrade this script, error: &8" + str(err) + " &cof type &8" + str(type(err)))
            printF("&cPlease check for updates manually at &b" + Constants.GITHUB_LINK)
            printF("&cAlternately, contact Noah for help at &bwww.noahf.net")
            printF(" ")
        return True

    def today(self, ui, args):
        try:
            possible_proxy = datetime.strptime(" ".join(args), "%B %d %Y") if len(args) > 0 else None
            string = ui.get_today_string(possible_proxy)
            printF(" ")
            if possible_proxy is not None:
                printF("&8&o(Proxy Date: " + str(" ".join(args)) + ")")
            printF(string)
            printF(" ")
        except Exception as err:
            printF("&cAn error occurred, possible invalid date? &8" + str(err))

        return True

    def version(self, ui, args):
        printF(" ")

        version = Updater.VERSION
        latest = str(ui.updater.latest_version)
        delta = ui.updater.delta_version
        dev = Updater.DEV_BUILD
        for index, arg in enumerate(args):
            if args[index - 1] == "--version":
                version = arg
            elif args[index - 1] == "--delta":
                delta = int(arg)
            elif args[index - 1] == "--latest":
                latest = arg
            elif args[index - 1] == "--dev-build":
                dev = bool(arg)
            elif args[index - 1] == "--reboot-as":
                self.restart(ui, ["--internal"] + args)
                return True
        
        if len(args) > 0 and "--detail" in args[0]:
            printF(f"Found version: {version}")
            printF(f"Latest version: {latest}")
            printF(f"Version History: {str(ui.updater.latest_history)}")
            printF(f"Delta: {str(delta)}")
            printF(f"Dev build: {str(dev).upper()}")
            printF(" ")
            return True

        printF(f"&fThis script is using ABDayDetector version {version} (Python {str(sys.version).split(' ')[0]}) (Is dev build? {str(dev).upper()})")
        if delta == 0:
            printF("&aYou are on the latest version!")
        elif delta > 0:
            printF(f"&eYou are {str(delta)} version{'' if delta == 1 else 's'} behind!")
            printF('&eUpdate by typing "&bupgrade&e"!')
        elif delta == -1:
            printF("&cError checking version status.")
            printF(f"&f&oCheck for updates manually at &b&n{Updater.CHECK_URL}")

        printF(" ")
        return True

    def logs(self, ui, args):
        printF(" ")
        printF("&6LOG HISTORY:")
        for index, line in enumerate(Log.get_log_history()):
            printF(f"&c[&e{str(index + 1)}&c] &7" + str(line))
        printF(" ")
        return True

    def share(self, ui, args):
        printF(" ")
        printF("&6SHARE THE PROGRAM:")
        printF("&b&n" + Constants.GITHUB_LINK)
        printF(" ")
        printF("&7&oSharing the program to other people helps out a lot with making others aware of this extremely useful program. Speaking as the developer of this script, it really makes me happy to see more people using this regularly as I have had no other incentive to make this other than to help others. Thank you for using this script!")
        printF(" ")
        return True

    def show_days(self, ui, args):
        days_off = {}
        last_index = 0
        last_day = None
        for index, key in enumerate(ui.assigner.get_days_off()):
            # Feb 12 2024: Parent-Teacher Conf
            # Dec 16 2023 - Jan 2 2024:
            reason = ui.assigner.get_days_off()[key]
            is_multiple_days = last_day != None and as_epoch(key) - as_epoch(last_day) == 86400 and days_off[last_index]["reason"] == reason
            if is_multiple_days == True:
                days_off[last_index] = {
                    "from": days_off[last_index]["from"],
                    "to": key,
                    "reason": days_off[last_index]["reason"]
                }
                last_day = key
                continue
            last_index += 1
            if is_multiple_days == False:
                days_off[last_index] = {
                    "from": key,
                    "to": key,
                    "reason": reason
                }
            last_day = key

            
        now = datetime.now()
        now_epoch = as_epoch(now)
        printed = False

        def colorify(date):
            epoch = as_epoch(date)
            if epoch == now_epoch:
                return "&r&a"
            if epoch > now_epoch:
                return "&r&3"
            return "&r&c"

        def print_now():
            printF("&7&o" + now.strftime("%b " + ui.number_of(now) + " %Y") + ": " + ui.provide_information(now, prefix="", colored=False))
        
        printF(" ")
        printF(f"&6DAYS OFF: &7({str(len(days_off.keys()))})")
        for key in days_off.keys():
            from_date = days_off[key]["from"]
            to_date = days_off[key]["to"]
            reason = days_off[key]["reason"]
            
            try:
                if as_epoch(from_date) >= now_epoch and as_epoch(to_date) <= now_epoch:
                    printed = True

                date_before = as_epoch(days_off[key - 1]["from"]) if as_epoch(now) < as_epoch(ui.assigner.year_start) else as_epoch(ui.assigner.year_start)
                if printed == False and date_before < now_epoch and as_epoch(from_date) > now_epoch:
                    print_now()
                    printed = True

                prefix = colorify(from_date) + from_date.strftime("%b " + ui.number_of(from_date) + " %Y")
                if from_date != to_date:
                    prefix = prefix + " &7-> " + colorify(to_date) + to_date.strftime("%b " + ui.number_of(to_date) + " %Y")
                prefix = prefix + "&f: "
                
                printF(prefix + "&e" + reason)
            except Exception as err:
                try:
                    printF("&r&3" + from_date.strftime("%b " + ui.number_of(from_date) + " %Y") + " &7-> &r&3" + to_date.strftime("%b " + ui.number_of(to_date) + " %Y") + "&f: &e" + reason)
                except Exception as err2:
                    printF("&cAn error occurred: &8" + str(err2) + " caused by " + str(err))

        if printed == False:
            print_now()

        cd_total, sd_total = ui.assigner.get_total_days()
        cd_experienced, sd_experienced = ui.assigner.get_progression(now)
        cd_left, sd_left = cd_total - cd_experienced, sd_total - sd_experienced
        cd_percent, sd_percent = (cd_experienced / cd_total) * 100, (sd_experienced / sd_total) * 100

        cd_percent, sd_percent = round(cd_percent), round(sd_percent)

        current_a_day_index, current_b_day_index = 0, 0
        
        printF(" ")
        printF(f"&fSchool Days: &b{str(sd_experienced)}&7/&e{str(sd_total)} &f(&d{str(sd_percent)}%&f) (&a{str(sd_left)} &fleft)")
        printF(f"&fCalendar Days: &b{str(cd_experienced)}&7/&e{str(cd_total)} &f(&d{str(cd_percent)}%&f) (&a{str(cd_left)} &fleft)")
        printF(" ")
        return True
        
    def inspect(self, ui, args):
        printF(" ")
        printF("&6DETECTED TRACEBACK OF ERROR:")
        traceback.print_exception(type(ui.assigner.fatal_error), ui.assigner.fatal_error, ui.assigner.fatal_traceback)
        printF(" ")
        if Updater.FORCE_ERROR is not None:
            printF("&6FORCE ERROR:")
            printF(f"&fThis error was intentionally caused &e{str(Updater.FORCE_ERROR_LOCATIONS[Updater.FORCE_ERROR])}&f!")
            printF("&7&oRestart the program to resume normal use.")
            printF(" ")
        printF("&fView the logs by typing &blogs")
        printF(" ")
        return True

# the user interface
# the MOTD and instructions
# the command input
class UserInterface:
    # separators are how exactly you can specify multiple dates
    # for example:
    # January 1-31 2024 is just as valid as January 1>31 2024
    # January 1 2024 - Februrary 1 2024 will be just as valid as January 1 2024 > February 1 2024
    SEPARATORS = ["-", "/", "//", ">", "to", "|"]
    REGEX_SEPARATORS = "|".join(SEPARATORS)

    DATE_FORMATS = [
            "%B %d %Y",
            "%b %d %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%m-%d-%Y",
            "%m-%d-%y",
            "%m/%d/%y",
            "%m/%d/%Y"
        ]
    
    DATES_CHARACTER_MAP = { # "python date format": ["java simple date time", "regex"]
                "%B": ["MMMMM", "[A-Za-z]{3,}"],
                "%b": ["MMM", "[A-Za-z]{3}"],
                "%d": ["d", "\d{1,2}"],
                "%Y": ["YYYY", "\d{4}"],
                "%y": ["YY", "\d{2}"],
                "%m": ["MM", "\d{1,2}"]
        }
    
    def is_external():
        # detects if the user is running in IDLE or not (used for color support and whatnot)
        return False if 'idlelib.run' in sys.modules else True

    def color(string, keycode, color):
        string = string.replace(keycode, color if UserInterface.is_external() ==  True else "")
        return string

    def color_full(string):
        # yes these are minecraft: java edition color codes
        # no I refuse to give them up, I know them like the back of my hand
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
        # &r at the end because otherwise it will carry over into the next line (no flush?)
        print(UserInterface.color_full(string + "&r"))
    
    def __init__(self, ab_date_assigner: ABDateAssigner, commands: Commands, updater: Updater):
        self.assigner = ab_date_assigner
        self.commands = commands.conditional_register(self.assigner)
        self.updater = updater

        now = datetime.now()

        Log.text("Clearing console, as it's no longer needed for debugging purposes...")
        Log.text(" ")
        Log.text(" ")
        Log.text(" ")
        Log.text(" ")

        if not (len(sys.argv) > 1 and "--minimal" in sys.argv):
            cmd("cls")
            printF("&6SCHOOL DAY DETECTOR &8v" + Updater.VERSION + (" &r&c&l&n(DEVELOPER BUILD)" if Updater.DEV_BUILD == True else ""))
            printF("&e| &fWelcome to the the school day detector.")
            printF(" ")
            printF("&6WHAT?")
            printF("&e| &fThis program lets you figure out if a day is going to be an A day or a B day.")
            printF("&e| &fNOTE: The program will update its A/B day calculator with unexpected days off (e.g., snow) if they occur.")
            printF(" ")
            if self.assigner.fatal_error is None:
                printF("&6HOW?")
                printF("&e| &fEnter a date below and the program will give you any and all information about it.")
                printF("&e| &fType &bhelp &fto view all the commands you can utilize and available date formats.")
                printF("&e| &fType &bcontact &fif you need to contact Noah if you find any bugs or issues.")
                printF("&e|  ")
                printF("&e|   &r&6A SINGLE DATE:")
                printF("&e|   &r&5| &fThe format should be: &aMONTH DAY YEAR")
                printF("&e|   &r&5| &fFor example: &r&3" + now.strftime("%B " + self.number_of(now) + " %Y"))
                printF("&e|  ")
                printF("&e|   &r&6MULTIPLE DATES:")
                printF("&e|   &r&5| &fThe format should be: &aMONTH DAY YEAR - MONTH DAY YEAR")
                printF("&e|   &r&5| &fFor example: &r&3" + now.strftime("%B") + " 1 " + now.strftime("%Y") + " - " + now.strftime("%B") + " " + str(get_last_day_of_month(now).day) + " " + now.strftime("%Y"))
            else:
                printF("&6BUT HOLD ON!")
                printF("&e| &fIt seems a fatal error occurred while trying to grab and/or calculate the necessary information.")
                printF("&e| &fUnfortunately, &cthis means the program cannot continue as intended.")
                printF("&e| &fMost features have been disabled to prevent crashes.")
                printF("&e|  ")
                printF("&e|   &r&6SOLUTIONS:")
                printF("&e|   &r&5| &fEnsure you are connected to a stable internet connection.")
                printF("&e|   &r&5| &fCheck if the program is outdated by typing &bversion&f.")
                printF("&e|   &r&5|     &7&o(If outdated, consider upgrading by typing &b&oupgrade&7&o)")
                printF("&e|   &r&5| &fReinstall the program by typing &bupgrade force&f, which can fix a lot of issues.")
                printF("&e|   &r&5| &fContact the developer for any other issues by typing &bcontact&f.")
                printF("&e| ")
                printF(f"&e| &7&oDetected error: &8{str(self.assigner.fatal_error)}, see more with &b&oinspect")
            printF(" ")
            if self.updater.delta_version > 0: # user needs to update teehee
                printF("&6YOU ARE OUTDATED!")
                if self.updater.delta_version != -1:
                    printF(f"&e| &eYou are {str(self.updater.delta_version)} version(s) out of date!")
                printF("&e| &fCheck what version you're using by typing \"&bversion&f\"")
                printF("&e| &fUpgrade your script automatically by typing \"&bupgrade&f\" &c&l(RECOMMENDED ASAP)")
                printF(" ")
            try:
                printF(self.get_today_string())
            except Exception as err:
                printF("&cAn error occurred: &8(get_today_string) " + str(err))
            printF(" ")
        else:
            printF("Successfully started new instance: &6SCHOOL DAY DETECTOR &8v" + Updater.VERSION)
            printF(" ")
        self.ask_input()

    # removes the extra zero in %d strftime in datetime
    # like how it does November 01 2024
    # I don't like that so I made it left-strip it of any zeros
    def number_of(self, date):
        return date.strftime("%d").lstrip('0')

    def get_today_string(self, proxy_date=None):
        now = datetime.now() if proxy_date == None else proxy_date
        suffix = ""
        next_day = self.assigner.get_next_school_day(now)

        if as_epoch(now) > as_epoch(self.assigner.year_end) or as_epoch(now) < as_epoch(self.assigner.year_start):
            raise ValueError("currently not in a school year, can't show today text")

        if next_day is not None: #don't show next school day if it's not a school day lol
            suffix = " " + next_day.strftime("%A, %B " + self.number_of(next_day) + self.assigner.get_ordinal_ending(next_day.day)) + " will be " + self.provide_information(next_day, prefix="")
            
        return "&fToday is " + self.provide_information(now, prefix="") + "&f." + suffix

    def error(self, msg, err):
        printF(" ")
        printF(" ")
        printF("&cAN ERROR OCCURRED!")
        if not err == None:
            printF("&cWe found this error to be the possible culprit: &8" + str(err))
            printF("&c&oIt's possible you entered something wrong or the program is faulty (try updating if outdated)")
            printF("&cSupplementary Message: &8" + msg)
        else:
            printF("&cWe found this message relating to your error:")
            printF("&7&o" + str(msg))
        printF(" ")

        self.ask_input()


    # LEGAL INPUTS:
    # Jan 17, 2024
    # Jan 17-18, 2024
    # Jan 17, 2024 - Jan 18, 2024
    # Jan 17, 2024-Jan 18, 2024

    def date(self, string, date_format):
        return datetime.strptime(string, date_format)

    # searches an input string for a regex pattern
    def search_regex(self, input_text, pattern):
        return list(self.search_regex_complex(input_text, pattern).values())

    # returns a dictionary (map) of regex position matches along with what matched
    # for example:
    # input = "This is a 123 test"
    # pattern = "\d{3}" (3 digits in a row)
    # returned: {11: "123"}
    # the start index is the start of the string rather than the end
    def search_regex_complex(self, input_text, pattern):
        returned = {}
        for item in re.compile(pattern).finditer(input_text):
            returned[item.span()[0]] = item.group(0)
        return returned

    # check if a date can be parsed into a date format
    def is_date(self, string, date_format):
        try:
            self.date(string, date_format)
            return True
        except ValueError:
            return False

    # returns a list of indices of where dates of a certain format are located
    def find_dates(self, user_input, date_format, day_separators=None):
        try:
            returned = []
            original_format = date_format
            char_map = UserInterface.DATES_CHARACTER_MAP # for ease of access reasons
            for character in char_map: # make date format in a regular expression
                regex = char_map[character][1]
                if day_separators is not None and "d" in character:
                    for separator in day_separators:
                        date_format = date_format.replace(character, regex + separator + regex)
                date_format = date_format.replace(character, regex)

            dates_raw = self.search_regex(user_input, date_format)

            if len(dates_raw) == 0 and day_separators == None: # old method of Jan 1-31 2024
                dates_raw = self.find_dates(user_input, original_format, day_separators=[separator for separator in UserInterface.SEPARATORS if separator in user_input])

            if len(dates_raw) == 0:
                return []

            dates_and_separators = self.search_regex_complex(user_input, UserInterface.REGEX_SEPARATORS + "|" + date_format)
            next_date, separator, previous_date = None, False, None
            for index, key in enumerate(dates_and_separators):
                match = dates_and_separators.get(key)
                if match not in UserInterface.SEPARATORS:
                    if next_date is None and self.is_date(match, original_format):
                        next_date = self.date(match, original_format)
                    elif previous_date is None and separator == True and self.is_date(match, original_format):
                        previous_date = self.date(match, original_format)
                        
                        delta = (max(previous_date, next_date) - min(previous_date, next_date)).days
                        
                        for i in range(0, delta):
                            dates_raw.append(next_date)
                            next_date = next_date + timedelta(days=1)

                        next_date, separator, previous_date = None, False, None
                    continue

                separator = True


            dates = []
            for index, date in enumerate(dates_raw):
                if day_separators is None:
                    try:
                        dates.append(self.date(date, original_format) if type(date) is str else date)
                    except ValueError as err:
                        pass
                    continue

                for separator in day_separators:
                    located_regex = self.search_regex(user_input, "\d{1,2}" + separator + "\d{1,2}")[0]                
                    days = [int(i) for i in located_regex.split(separator)]

                date = self.date(user_input.replace(located_regex, "1"), original_format)

                month = date.month
                year = date.year

                dates = dates + [datetime(year=year, month=month, day=i) for i in range(min(days), max(days) + 1)]

            return dates
        except Exception as err:
            return []

    def finalize_and_sort_input(self, final_dates):
        if len(final_dates) == 1:
            return final_dates[0]

        final_dates = list(set(final_dates)) # remove duplicates

        dates = {}
        for date in final_dates:
            dates[as_epoch(date)] = date

        return [dates.get(key) for key in dict(sorted(dates.items())).keys()]

    def try_input(self, user_input):
        try:
         #   for date_format in self.date_formats:
           #     date = self.try_input(date, inputted, date_format.
            dates = []
            for date_format in UserInterface.DATE_FORMATS:
                found = self.find_dates(user_input, date_format)
                dates = dates + found

            dates = self.finalize_and_sort_input(dates)

            if isinstance(dates, list):
                if len(dates) == 0:
                    raise ValueError("Failed to find dates from input: '" + str(user_input) + "'")
                if len(dates) == 1:
                    dates = dates[0]

            return dates
        except Exception as err:
            return err if err.__context__ is None else err.__context__

    def ask_input(self, forced: str=None):
        try:
            inputted = input(UserInterface.color_full("&fEnter date or command: &b")) if forced == None else forced
        except KeyboardInterrupt as err:
            raise err
        except EOFError:
            inputted = ""

        if inputted.strip() == "":
            self.ask_input()
            return

        # execute any potential commands, if the evaluate func returns "True", we know it was a real command
        if self.commands.evaluate(self, inputted.strip()):
            self.ask_input()
            return
            
        if assigner.fatal_error:
            printF(" ")
            printF("&c&lFATAL ERROR")
            printF("&e| &fIt seems a fatal error occurred while trying to grab and/or calculate the necessary information.")
            printF("&e| &fUnfortunately, &cthis means the program cannot continue as intended.")
            printF("&e| &fMost features have been disabled to prevent crashes.")
            printF("&e|  ")
            printF("&e|   &r&6SOLUTIONS:")
            printF("&e|   &r&5| &fEnsure you are connected to a stable internet connection.")
            printF("&e|   &r&5| &fCheck if the program is outdated by typing &bversion&f.")
            printF("&e|   &r&5|     &7&o(If outdated, consider upgrading by typing &b&oupgrade&7&o)")
            printF("&e|   &r&5| &fReinstall the program by typing &bupgrade force&f, which can fix a lot of issues.")
            printF("&e|   &r&5| &fContact the developer for any other issues by typing &bcontact&f.")
            printF("&e| ")
            printF(f"&e| &7&oDetected error: &8{str(self.assigner.fatal_error)}, see more with &b&oinspect")
            printF(" ")
            self.ask_input()
            return

        # remove ordinals from date input as they could be not allowed
        # for example: January 1st, 2024 (illegal input) -> January 1, 2024 (valid input)
        for ordinal in ["st", "nd", "rd", "th"]:
            inputted = inputted.replace(ordinal, "")

        # trying different input dates as the user may have their preference
        date = self.try_input(inputted)

        if isinstance(date, Exception) or date == None:
            if isinstance(date, ValueError) and ("does not match format" in str(date) or "Failed to find date" in str(date)):
                self.error("You entered an incorrect date format or command.\nTry typing \"&nhelp&r&7&o\" for help.", None)
                return
            self.error("Standard error of type " + str(type(date)), date)
            return

        printF(" ")
        printF(" ")
        try:
            if isinstance(date, list):
                for item in date:
                    self.print_information(item, True)
                printF(" ")
            else:
                self.print_information(date)
        except Exception as err:
            self.error("Standard error of type " + str(type(date)) + " during print information", date)

        self.ask_input()

    def provide_information(self, date, prefix=None, colored=True):
        date_type = self.assigner.get_date_type(date)
        day_letter = self.assigner.get_day_letter(date)
        day_off_reason = self.assigner.get_day_off_reason(date)
        
        prefix = (("That day is " if isinstance(date, list) == False else "") if prefix == None else prefix) + ("&r" if colored==True else "")
        
        if not day_letter == None:
            return prefix + (("&c" if colored==True else "") if day_letter == DayLetter.A_DAY else ("&9" if colored==True else "")) + DayLetter.format(day_letter)
        elif not day_off_reason == None:
            return prefix + ("&e" if colored==True else "") + day_off_reason
        if date_type == DateType.OUT_OF_SCOPE:
            return prefix + ("&4" if colored==True else "") + "not in this school year"
        else:
            return prefix + ("&2" if colored==True else "") + DateType.format(date_type)
        raise RuntimeError("Information was not handled nor provided correctly to self.provide_information")

    def print_information(self, inputted_date, list_element=False):
        if not isinstance(inputted_date, list):
            inputted_date = [inputted_date] # format as list

        items = []
        for date in inputted_date:
            day = Constants.DAYS[date.weekday()].upper()
            items.append(
                [("&6&n" + (day[0:3] if list_element == True else day) + ", " + (Constants.MONTHS[date.month - 1].upper()[0:3] if list_element == True else Constants.MONTHS[date.month - 1].upper()) + " " + str(date.day) + self.assigner.get_ordinal_ending(date.day).upper() + ", " + str(date.year)),
                (self.provide_information(date)),
                 " "]
            )

        for item in items:
            if list_element == True:
                printF("&r ".join(item))
                continue
            
            for date in item:
                printF(date)

# program start
if __name__ == "__main__":
    using_windows = "Windows" in platform.system()
    if not using_windows:
        print("** This program recommends Windows to run. **")
        print("** Not using Windows can result in broken functality or glitches. **")
        print("** Proceed with caution. The program will boot in 5 seconds. **")
        print(" ")
        threadcontrol.sleep(5)
    start = datetime.now()
    Log.text("Loading program...")
    try:
        Log.text("Date and time: " + str(datetime.now()))
        if not using_windows:
            text = "** USER IS NOT USING WINDOWS. SOME FUNCTIONALITY MAY BE LIMITED OR BROKEN. **"
            
            Log.text("*" * len(text))
            Log.text(text)
            Log.text("*" * len(text))
        Log.text("Main file: " + os.path.basename(__file__) + " (path: " + str(__file__) + ")")
        Log.text("Is non-IDLE? " + str(UserInterface.is_external()))
        Log.text("Loading color and title...")
        cmd("color") # necessary on windows 10 I believe
        cmd(f"title School Day Detector - Booting Program...")

        Log.text("Still in __name__ (" + str(__name__) + "), instantiating valued classes...")
        updater = Updater()
        assigner = ABDateAssigner()
        commands = Commands()

        cmd(f"title School Day Detector v{Updater.VERSION}")
        
        Log.text("Enjoy the program, made with <3 by Noah Franks")
        Log.text("| -> MAIN WEBSITE: www.noahf.net")
        Log.text("| -> LET'S GO TERRIERS!") # WBHS!!!!!!!!!
        Log.text("| -> LET'S GO HOKIES!") # VT!!!!!!!!
        Log.text("| -> CREATED IN JAN 2024") # modified in the following months
        Log.text(f"| -> TOOK {str(datetime.now() - start)} TO START")

        Log.text("Instantiating UserInterface...")

        ui = UserInterface(assigner, commands, updater)
    except KeyboardInterrupt as err:
        try:
            print(" ")
            print(" ")
            printF("&cYou pressed &bCTRL + C &coutside of an update, this will close the program...")
            printF("&7&oPress CTLR + C again to restart")
            threadcontrol.sleep(1)
            printF("&e&oClosing in &c3s&e...")
            threadcontrol.sleep(1)
            printF("&e&oClosing in &c2s&e...")
            threadcontrol.sleep(1)
            printF("&e&oClosing in &c1s&e...")
            threadcontrol.sleep(1)
            printF("&a&oExiting program")
            threadcontrol.sleep(0.5)
            exit()
        except KeyboardInterrupt as err:
            printF("&a&oRestarting...")
            threadcontrol.sleep(0.1)
            os.startfile(__file__)
            exit()
            print("You may close this terminal window!")
    except Exception as err:
        print(" ")
        try:
            print(traceback.format_exc())
        except Exception as err:
            print("(No traceback: " + err)
        print("A fatal exception has occurred. The program will exit momentary.")
        print("Found error that may be related: " + str(err))

    cmd("pause >NUL")


    # see some old code when I was initally testing in VERY mid January:
    #test_day = datetime(month=1, day=17, year=2024)
    
    #print("DATE TYPE: " + str(DateType.value_of(assigner.get_date_type(test_day))))
    #print("DAY OFF REASON: " + str(assigner.get_day_off_reason(test_day)))
    #print("DAY LETTER: " + str(DayLetter.value_of(assigner.get_day_letter(test_day))))
