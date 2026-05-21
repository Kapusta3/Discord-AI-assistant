import datetime
from colorama import init, Fore

init(autoreset=True)

def get_current_time():
    print(f"{Fore.CYAN}[GET_CURRENT_TIME Usage]: Searching current time : real[{datetime.datetime.now()}]")
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")