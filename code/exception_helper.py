from __future__ import print_function

## Todo reimplement this whole module and make it not garbage

import sys
import time
import traceback

from utilities import Utilities
try:
    from mail_to_sms import MailToSMS
except ImportError as e:
    MailToSMS = False
    print("Optional module mail_to_sms not found. SMS alert disabled.", e)


class Thread_Tracker:
    def __init__(self, thread, event):
        self.thread = thread
        self.event = event


## TODO: lots of try-except blocks
class ExceptionHelper:
    ## Literals
    LOG_TIME = "log_time"
    STD_STREAM = "std_stream"
    TIME_FORMAT = "time_format"
    ALERT = "alert"
    MAIL_TO_SMS_CFG_NAME = "mail.json"
    MAIL_TO_SMS_CFG_PATH = Utilities.build_path_from_config(MAIL_TO_SMS_CFG_NAME)

    ## Globals
    DEFAULT_TIME_FORMAT = "%X %x"
    ATTEMPT_LIMIT = 10
    ATTEMPT_COOLDOWN = 30
    SLEEP_TIME = 10
    ALERT_DEFAULT = True


    def __init__(self, **kwargs):
        self.static = ExceptionHelper

        self.mail_to_sms_cfg = Utilities.load_json(self.static.MAIL_TO_SMS_CFG_PATH)

        self.alert_state = kwargs.get(self.static.ALERT, self.static.ALERT_DEFAULT)
        self.log_time = kwargs.get(self.static.LOG_TIME, True)
        self.std_stream = kwargs.get(self.static.STD_STREAM, sys.stdout)
        self.time_format = kwargs.get(self.static.TIME_FORMAT,
                                      self.static.DEFAULT_TIME_FORMAT)


    def print(self, exception, *args, **kwargs):
        output = ""
        exit = False

        ## Log the current time if necessary
        if(self.log_time):
            output += "[{0}]".format(self._get_current_time_str())

        ## Use specified std stream (but don't overwrite the current stream if it exists)
        if("file" not in kwargs and self.std_stream):
            kwargs["file"] = self.std_stream

        ## TODO: better exception formatting?
        if(not exception):
            exception = ""

        ## Determine if the exit kwarg is supplied
        if("exit" in kwargs):
            if(kwargs["exit"] == True):
                exit = True
                del kwargs["exit"]

        ## Actual output
        print(output, exception, *args, **kwargs)

        ## Flush the output
        sys.stdout.flush()


        if(kwargs.get("alert", False)):
            self.alert()

        ## Exit if necessary
        if(exit):
            self.exit()


    def print_stdout(self, exception, *args, **kwargs):
        self.print(exception, *args, file=sys.stdout, **kwargs)


    def print_stderr(self, exception, *args, **kwargs):
        self.print(exception, *args, file=sys.stderr, **kwargs)


    def exit(self):
        sys.exit()


    def _get_current_time_str(self):
        return time.strftime(self.time_format)


    def _send_alert(self, message):
        if(not MailToSMS or not self.alert_state):
            return

        cfg = self.mail_to_sms_cfg

        try:
            MailToSMS(cfg["number"], cfg["carrier"], cfg["username"], cfg["password"], message)
        except Exception as e:
            self.print(e, "Unable to send message")



    ## TODO: better word than 'robust'
    ## TODO: stick this in separate thread? 
    def make_robust(self, non_robust_function, allowed_exceptions, allowed_exception_callback, exception_callback, *non_robust_args):
        last_exception_time = 0
        attempts = 0
        continue_loop = True
        while(continue_loop and attempts < self.static.ATTEMPT_LIMIT):
            try:
                non_robust_function(*non_robust_args)
            except (allowed_exceptions) as e:
                ## Print out the exception that just occurred
                self.print(e, "Allowed exception just occured in make_robust")

                ## Send exception to the callback
                allowed_exception_callback(e)

                ## If the last exception happened > ATTEMPT_COOLDOWN seconds
                ##  then decrement the counter (if possible). This makes it
                ##  so that the loop won't go on for forever. This algorithm
                ##  isn't perfect, but it works okayish.
                if(last_exception_time + self.static.ATTEMPT_COOLDOWN < time.time() and attempts > 0):
                    attempts -= 1
                else:
                    attempts += 1
                last_exception_time = time.time()
            except Exception as e:
                ## Print out the exception that just occurred
                self.print(e, "Unexpected error just occured in make_robust")

                ## Send exception to the callback
                exception_callback(e)

                ## End the loop
                continue_loop = False
