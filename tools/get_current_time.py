import datetime
from colorama import init, Fore
from config import Debug

init(autoreset=True)

def get_current_time():
    if Debug:
        print(f"{Fore.CYAN}[GET_CURRENT_TIME Usage]: Searching current time : real[{datetime.datetime.now()}]")
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")