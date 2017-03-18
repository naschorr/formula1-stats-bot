from __future__ import print_function

import sys
import os
import psutil
import click
import subprocess

## Put the code/ dir into the python path
sys.path.append(os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-1] + ["code"]))

from utilities import Utilities
from scraper import Scraper
from flair_scraper import FlairScraper
from db_controller import DB_Controller
from exception_helper import ExceptionHelper

if(os.name == "nt"):
    VIRTUALENV_ACTIVATE_PATH = Utilities.build_path_from_root("Scripts", "activate_this.py")
else:
    VIRTUALENV_ACTIVATE_PATH = Utilities.build_path_from_root("bin", "activate_this.py")

## Activate the virtualenv in this script
exec(compile(open(VIRTUALENV_ACTIVATE_PATH, "rb").read(), VIRTUALENV_ACTIVATE_PATH, 'exec'))


class RF1_Stats_Bot:
    ## Literals
    NAME = "rf1-stats-bot"
    TEMP_FILE_NAME = "tmp"

    ## Globals
    POSTGRES_VERSION = 9.1
    PROCESS_KILL_TIMEOUT = 5
    PID_FILE_NAME = NAME + ".pid"
    PID_FILE_PATH = Utilities.build_path_from_root(TEMP_FILE_NAME, PID_FILE_NAME)
    ERR_LOG_NAME = "err.log"
    ERR_LOG_PATH = Utilities.build_path_from_root(TEMP_FILE_NAME, ERR_LOG_NAME)

    def __init__(self, *args, **kwargs):
        self.static = RF1_Stats_Bot
        self.pid = None

        ## Make sure the temp file is available
        try:
            os.makedirs(Utilities.build_path_from_root(self.static.TEMP_FILE_NAME))
        except FileExistsError as e:
            pass    # File exists, no worries

        self.exception_helper = ExceptionHelper(**kwargs)

        if(kwargs.get("stop", False)):
            self._stop()
        elif(kwargs.get("start", False)):
            self._start(**kwargs)
        elif(kwargs.get("pid", False)):
            print(self.pid)
        elif(kwargs.get("flair_scraper", False)):
            self._start_flair_scraper()
        else:
            self._start()

    ## PID Getters / Setters

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, value):
        try:
            value = int(value)
            if(value <= 0):
                value = None
        except Exception as e:
            value = None

        self._pid = value

    ## Methods

    def _start(self, *args, **kwargs):
        if(not kwargs.get("remote", False) and not self._is_postgres_running()):
            self.exception_helper.print(None, "Postgres isn't running. Exiting.", exit=True)

        if(self._is_running()):
            self.exception_helper.print(None, 
                                        "{0} is already running. Exiting.".format(self.static.NAME),
                                        exit=True)

        try:
            pid = psutil.Process()  ## Pid of this process
            self.pid = pid
            self._save_pid_file()

            Scraper(**kwargs)
        finally:
            self._cleanup()


    def _stop():
        self._get_pid_file()
        process = psutil.Process(self.pid)
        try:
            process.terminate()
            process.wait(self.static.PROCESS_KILL_TIMEOUT)
            return
        except psutil.NoSuchProcess as e:
            self.exception_helper.print(e, "Process doesn't exist. Exiting.", exit=True)
        except psutil.TimeoutExpired as e:
            self.exception_helper.print(e, "Process termination expired, trying to kill now.")
            process.kill()
        finally:
            self._cleanup()


    def _start_flair_scraper(self, *args, **kwargs):
        overwrite = kwargs.get("overwrite", False)
        FlairScraper(overwrite)


    def _cleanup(self):
        self.pid = None
        self._save_pid_file()


    def _save_pid_file(self):
        pid_path = self.static.PID_FILE_PATH
        pid = self.pid
        if(not pid):
                os.remove(pid_path)
                open(pid_path, "w").close()
        else:
            with open(pid_path, "w") as pid_file:
                    pid_file.write(pid)


    def _get_pid_file(self):
        with open(self.static.PID_FILE_PATH, "r") as pid_file:
            try:
                self.pid = int(pid_file.read())
            except ValueError as e:
                self.pid = None


    def _is_running(self):
        self._get_pid_file()
        if(not self.pid):
            return False
        elif(psutil.pid_exists(self.pid)):
            return True
        else:   ## pid file has a pid in it, but no process has that pid
            self.exception_helper.print(None,
                                        "Pid in {0}, but no process attached. This shouldn't \
                                        happen. Cleaning up.".format(self.static.PID_FILE_PATH))
            self._cleanup()
            return False


    def _is_postgres_running(self):
        if(os.name == "nt"):
            return any([proc.name() in "postgresql" for proc in psutil.process_iter()])
        else:
            try:
                if(self.static.POSTGRES_VERSION in subprocess.check_output(["service", 
                                                                            "postgresql", 
                                                                            "status"])):
                    return True
            except subprocess.CalledProcessError as e:
                self.exception_helper.print(e, "Postgres isn't running", 
                                            "Returned error code: {0}, and output: {1}".format(e.returncode, e.output))
            finally:
                return False


@click.command()
@click.option("--start", is_flag=True, help="Starts the scraper normally")
@click.option("--quiet", is_flag=True, help="Starts the scraper quietly (no stdout)")
@click.option("--stop", is_flag=True, help="Stops the scraper process")
@click.option("--overwrite", is_flag=True, help="Overwrites any existing files when outputting {0}".format(FlairScraper.FLAIR_JSON_NAME))
@click.option("--flair-scraper", is_flag=True, help="Starts the flair scraper")
@click.option("--pid", "-p", is_flag=True, help="Shows the pid of the scraper process")
@click.option("--remote", "-r", is_flag=True, help="Denotes whether or not the scraper is accessing the database remotely (using {0} instead of {1})".format(DB_Controller.REMOTE_DB_CFG_NAME, DB_Controller.DB_CFG_NAME))
def main(start, quiet, stop, flair_scraper, overwrite, pid, remote):
    kwargs = {
        "start": start, "quiet": quiet, "stop": stop, 
        "flair_scraper": flair_scraper, "pid": pid, "remote": remote
    }

    ## TODO: remote these debug overrides
    kwargs["start"] = True
    kwargs["remote"] = True

    RF1_Stats_Bot(**kwargs)


if __name__ == "__main__":
    main()