from enum import Enum

LINE_UP = "\u001b[1A"
LINE_CLEAR = "\u001b[2K"


class Fore:
    RESET = "\u001b[0m"
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    YELLOW = "\u001b[33m"
    BLUE = "\u001b[34m"


class Result(str, Enum):
    ACTIVE = "active"
    EXCEPTION = "exception"
    INVALID = "invalid"
    RELISTED = "relisted"
    RENEWED = "renewed"
    REPOSTED = "reposted"

    @property
    def with_color(self):
        color_map = {
            Result.ACTIVE: Fore.BLUE,
            Result.EXCEPTION: Fore.RED,
            Result.INVALID: Fore.YELLOW,
            Result.RELISTED: Fore.GREEN,
            Result.REPOSTED: Fore.GREEN,
            Result.RENEWED: Fore.GREEN,
        }

        return f"{color_map[self]}{self}{Fore.RESET}"


# TODO making logging a part of this function
def reprint(*args, overwrite=False, **kwargs):
    if overwrite:
        print(LINE_UP, end=LINE_CLEAR, flush=True)

    print(*args, **kwargs, flush=True)
