# needed:
# requests
# tqdm

import os
import sys
import importlib
import traceback
import json
import time as threadcontrol

def cmd(command):
    if is_external():
        os.system(command)

def is_external():
    return False if 'idlelib.run' in sys.modules else True

def color(string, keycode, color):
    string = string.replace(keycode, color if is_external() ==  True else "")
    return string

def color_full(string):
    string = color(string, "&0", "\u001b[30m")
    string = color(string, "&1", "\u001b[34m")
    string = color(string, "&2", "\u001b[32m")
    string = color(string, "&3", "\u001b[36m")
    string = color(string, "&4", "\u001b[31m")
    string = color(string, "&5", "\u001b[35m")
    string = color(string, "&6", "\u001b[33m")
    string = color(string, "&7", "\u001b[37m")
    string = color(string, "&8", "\u001b[30;1m")
    string = color(string, "&9", "\u001b[34;1m")
    string = color(string, "&a", "\u001b[32;1m")
    string = color(string, "&b", "\u001b[36;1m")
    string = color(string, "&c", "\u001b[31;1m")
    string = color(string, "&d", "\u001b[35;1m")
    string = color(string, "&e", "\u001b[33;1m")
    string = color(string, "&f", "\u001b[37;1m")
    string = color(string, "&l", "\u001b[1m")
    string = color(string, "&n", "\u001b[4m")
    string = color(string, "&h", "\u001b[7m")
    string = color(string, "&r", "\u001b[0m")
    string = color(string, "&o", "\u001b[3m")
    return string

def printF(string):
    print(color_full(string + "&r"))

def ask_input(directions, denied_func):
    inputted = input(color_full(directions + "&b"))
    CONSENT = ["yes", "y", "yep", "okay", "yeah", "ye", "confirm", "agree", "agreed"]
    if inputted.lower() in CONSENT:
        return True

    denied_func()

def file_denied():
    printF(" ")
    printF("&c&l&nYou have declined an important file download.")
    printF("&fBy doing this, you &c&ncannot&r &futilize this program.")
    printF("&fRe-run the script if you would like to reconsider.")
    printF("&fOtherwise, thank you for checking this out, goodbye...")
    printF("&7&oPress any key to exit.")
    cmd("pause >NUL")
    exit()

def try_import(name, import_name, import_string):
    try:
        importlib.import_module(import_name)
        printF("&a✓ &fModule dependency satisfied: " + str(name) + import_string)
        return True
    except ModuleNotFoundError:
        return False
    except Exception as err:
        raise err

def ask_dependency(name, import_name, desc):
    real_name = import_name
    import_name = (" &8(" + str(import_name) + ")" if name != import_name else "")
    if try_import(name, real_name, import_name) == True:
        return

    printF("&bDEPENDENCY INSTALLATION REQUEST:")
    printF("&fThis script would like to install: &r&a" + str(name) + import_name)
    printF("&fThe script provided this explanation:")
    printF("&e>  &r&7" + str(desc))
    printF(" ")
    ask_input("&fWould you like to install '&b" + str(name) + "&f' (&aY&f/&cN&f)? ", file_denied)
    printF(" ")
    printF("&fDownloading and installing " + str(name) + import_name + "...")
    os.system("python -m pip install " + str(real_name) + " >null 2>&1")
    if try_import(name, real_name, import_name) == False:
        printF("&cFailed to install dependency: " + str(name) + import_name)
        printF("&cContact Noah at &bwww.noahf.net")
        printF("&7&oPress any key to exit...")
        cmd("pause >NUL")
        return
    printF(" ")

if __name__ == "__main__":
    try:
        cmd("title Install: SCHOOL DAY DETECTOR (ABDayDetector.py)")

        printF("&6SCHOOL DAY DETECTOR: &b&lINSTALLER")
        printF("&e| &fWelcome to the the school day detector INSTALLER.")
        printF(" ")
        printF("&6INSTALL PROGRAM:")
        printF("&e| &fYou are going to install the School Day Detector program for RCPS.")
        printF("&e| &fThis process should be pretty painless and easy.")
        printF("&e| &fFollow the prompts, you can type '&aY&f' for yes and '&cN&f' for no.")
        printF(" ")
        printF("&6NOTE ABOUT CONSENT:")
        printF("&e| &fBy not consenting to a required dependency installation, &c&nyou will not be able to use this program.")
        printF(" ")
        printF(" ")
        ask_input("&fDo you understand the directions (&aY&f/&cN&f)? ", exit)
        printF("&2Great! &fLet's see what files are needed to install.", )
        printF(" ")
        ask_dependency("requests", "requests", "We use this library to contact the Roanoke County Public Schools website for the data it contains about what school days the school has off, which is crucial in determining A/B day. It is also used to check for script updates.")
        printF(" ")
        ask_dependency("taqaddum", "tqdm", "We use this library to display a progress bar whenever a piece of data is downloading, such as when the script retrieves it's A/B day schedule from the RCPS website at www.rcps.us.")
        printF(" ")
        printF("&bSCRIPT INSTALLATION:")
        printF("&fNow, we need your permission to install the actual script.")
        printF("&fThis will delete this install.py file and let you use the main package.")
        printF("&7&o(Denying this will prevent the actual script from installing)")
        printF(" ")
        ask_input("&fWould you like to install the main script (&aY&f/&cN&f)? ", file_denied)

        import requests # should be installed now
        try:
            download = requests.get("https://update.ab.download.noahf.net/").text
            json_data = json.loads(request)
        except Exception as err:
            printF("&8(failed to retrieve actual script, ignorantly assuming files and folders)")
            json_data = {
                "tree": [
                    {"path": "ABDayDetector.py"}
                ]
            }

        FOLDER = "https://raw.githubusercontent.com/nfranks8036/ABDayDetectorScript/main/src/"

        tree = json_data["tree"]
        main = None
        for file in tree:
            url = FOLDER + str(file["path"])
            path = str(file["path"])

            download = requests.get(url).text
            with open(path, "w") as file:
                file.write(download)
                if path == "ABDayDetector.py":
                    main = path

        if main == None:
            raise RuntimeError("Failed to find main file, maybe it's not the same string (by literal)?")

        printF("&a✓ &fDownloaded main script.")
        printF(" ")
        printF(" ")
        printF("&6BOOM!")
        printF("&e| &fYou're done! You just finished installing the correct files and dependencies.")
        printF("&e| &fIf you ever want to run the script, double-click on \"&bABDayDetector&f\".")
        printF("&e| &fFollow the directions when you open that script to utilize it!")
        printF(" ")
        printF("&7&oPress any key to open the main script and close this one! (or, you could just close this tab)")
        os.remove(__file__)
        cmd("pause >NUL")

        os.startfile(main)
        exit()
    except Exception as err:
        printF(" ")
        printF("&cERROR TRACEBACK:")
        printF("&7" + traceback.format_exc().strip())
        printF(" ")
        printF("&c" + ("*" * 70))
        printF("&cA fatal exception has occurred!")
        printF("&cFailed to download and install the script.")
        printF("&cContact &bwww.noahf.net &cfor help.")
        printF(" ")
        printF("&cError (type: &8" + str(type(err)) + "&c): &8" + str(err))
        printF("&c" + ("*" * 70))
        printF("&7&oPress any key to exit!")
        cmd("pause >NUL")