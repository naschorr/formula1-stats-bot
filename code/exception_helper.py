from __future__ import print_function

import sys
import time
import threading

## TODO: lots of try-except blocks
class Exception_Helper:
    ## Literals
    LOG_TIME = "log_time"
    STD_STREAM = "std_stream"
    TIME_FORMAT = "time_format"

    ## Globals
    DEFAULT_TIME_FORMAT = "%X %x"
    ATTEMPT_LIMIT = 10
    ATTEMPT_COOLDOWN = 30
    SLEEP_TIME = 10

    def __init__(self, **kwargs):
        def getKwarg(kwarg, default=None):
            if(kwarg in kwargs):
                return kwargs[kwarg]
            else:
                return default

        self.log_time = getKwarg(Exception_Helper.LOG_TIME)
        self.std_stream = getKwarg(Exception_Helper.STD_STREAM)
        self.time_format = getKwarg(Exception_Helper.TIME_FORMAT, 
                                    Exception_Helper.DEFAULT_TIME_FORMAT)


    def print(self, exception, *args, **kwargs):
        output = ""

        ## Log the current time if necessary
        if(self.log_time):
            output += "[{0}]".format(self._get_current_time_str())

        ## Use specified std stream (but don't overwrite the current stream if it exists)
        if("file" not in kwargs and self.std_stream):
            kwargs["file"] = self.std_stream

        ## TODO: better exception formatting?
        if(not exception):
            exception = ""

        print(output, exception, *args, **kwargs)

        if("exit" in kwargs):
            if(kwargs["exit"] == True):
                self.exit()


    def print_stdout(self, exception, *args, **kwargs):
        self.print(exception, *args, file=sys.stdout, **kwargs)


    def print_stderr(self, exception, *args, **kwargs):
        self.print(exception, *args, file=sys.stderr, **kwargs)


    def exit(self):
        sys.exit()


    def _get_current_time_str(self):
        return time.strftime(self.time_format)


    def make_robust(self, non_robust_function, allowed_exceptions, allowed_exception_callback, exception_callback, *non_robust_args):
        thread = threading.Thread(target=self._init_make_robust, args=(non_robust_function, allowed_exceptions, allowed_exception_callback, exception_callback, *non_robust_args))
        thread.start()
        return thread


    def _init_make_robust(self, non_robust_function, allowed_exceptions, allowed_exception_callback, exception_callback, *non_robust_args):
        last_exception_time = 0
        attempts = 0
        continue_loop = True
        while(continue_loop and attempts < Exception_Helper.ATTEMPT_LIMIT):
            try:
                non_robust_function(*non_robust_args)
            except (allowed_exceptions) as e:
                ## Send exception to the callback
                allowed_exception_callback(e)

                ## If the last exception happened > ATTEMPT_COOLDOWN seconds
                ##  then decrement the counter (if possible). This makes it
                ##  so that the loop won't go on for forever. This algorithm
                ##  isn't perfect, but it works okayish.
                if(last_exception_time + Exception_Helper.ATTEMPT_COOLDOWN < time.time() and attempts > 0):
                    attempts -= 1
                else:
                    attempts += 1
                last_exception_time = time.time()
            except Exception as e:
                exception_callback(e)
                continue_loop = False