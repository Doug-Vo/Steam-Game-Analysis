import colorama
import os
import logging



colorama.init(autoreset= True)
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING' : colorama.Fore.YELLOW, 
        'INFO' : colorama.Fore.GREEN,
        'ERROR': colorama.Fore.RED 
}
    
    def format(self, record):
        log_message = super().format(record)
        return self.COLORS.get(record.levelname, '') + log_message
    
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers(): logger.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)