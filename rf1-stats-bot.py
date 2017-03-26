#!/usr/bin/python

from __future__ import print_function

import sys
import os
import subprocess

## Build path to the root directory (without utilities.py)
ROOT_DIR = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-1])

## Build the path to the virtualenv activation script
if(os.name == "nt"):
    VIRTUALENV_ACTIVATE_PATH = os.path.sep.join([ROOT_DIR, "Scripts", "activate_this.py"])
else:
    VIRTUALENV_ACTIVATE_PATH = os.path.sep.join([ROOT_DIR, "bin", "activate_this.py"])

## Activate the virtualenv in this interpreter
if(sys.version_info[0] >= 3):
    exec(compile(open(VIRTUALENV_ACTIVATE_PATH, "rb").read(), VIRTUALENV_ACTIVATE_PATH, 'exec'))
else:
    execfile(VIRTUALENV_ACTIVATE_PATH, dict(__file__=VIRTUALENV_ACTIVATE_PATH))

## Load virtualenv specific modules
import psutil
import click

## Put the code/ dir into the python path
sys.path.append(os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-1] + ["code"]))

## Finally, load all modules used for this program
from utilities import Utilities
from scraper import Scraper
from db_controller import DB_Controller
from exception_helper import ExceptionHelper
from flair_scraper import FlairScraper


class RF1_Stats_Bot:
    ## Literals
    NAME = "rf1-stats-bot"
    TEMP_FILE_NAME = "tmp"

    ## Globals
    POSTGRES_VERSION = "9.1"
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
        except OSError as e:    # FileExistsError for Python < 3
            if(e.errno == 17):
                pass    # File exists, no worries
        except FileExistsError as e:    # FileExistsError for Python > 3
            pass

        self.exception_helper = ExceptionHelper(**kwargs)

        if(kwargs.get("stop", False)):
            self._stop()
        elif(kwargs.get("start", False)):
            self._start(**kwargs)
        elif(kwargs.get("restart", False)):
            self._stop()
            self._start(**kwargs)
        elif(kwargs.get("status", False)):
            if(self._is_running()):
                print("{0} running with PID: {1}".format(self.static.NAME, self.pid))
            else:
                print("{0} isn't running".format(self.static.NAME))
        elif(kwargs.get("pid", False)):
            self._get_pid_file()
            print(self.pid)
        elif(kwargs.get("rows", False)):
            print(self._get_row_count(**kwargs))
        elif(kwargs.get("flair_scraper", False)):
            self._start_flair_scraper(**kwargs)
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
            pid = psutil.Process().pid  ## Pid of this process
            self.pid = pid
            self._save_pid_file()

            Scraper(**kwargs)
        finally:
            self._cleanup()


    def _stop(self):
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


    def _get_row_count(self, **kwargs):
        kwargs["suppress_greeting"] = True
        return DB_Controller(**kwargs).count_rows()


    def _start_flair_scraper(self, **kwargs):
	print("FS, ", kwargs)
        FlairScraper(**kwargs)


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
                    pid_file.write(str(pid))


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
                if(self.static.POSTGRES_VERSION in subprocess.check_output(["/usr/sbin/service", 
                                                                            "postgresql",
                                                                            "status"])):
                    return True
                else:
                    return False
            except subprocess.CalledProcessError as e:
                self.exception_helper.print(e, "Postgres isn't running", 
                                            "Returned error code: {0}, and output: {1}".format(e.returncode, e.output))
                return False


@click.command()
@click.option("--start", is_flag=True, help="Starts the scraper normally")
@click.option("--quiet", is_flag=True, help="Starts the scraper quietly (no stdout)")
@click.option("--stop", is_flag=True, help="Stops the scraper process")
@click.option("--restart", is_flag=True, help="Restarts the scraper")
@click.option("--status", is_flag=True, help="A more human readable --pid")
@click.option("--overwrite", is_flag=True, help="Overwrites any existing files when outputting {0}".format(FlairScraper.FLAIR_JSON_NAME))
@click.option("--flair-scraper", is_flag=True, help="Starts the flair scraper")
@click.option("--pid", "-p", is_flag=True, help="Shows the pid of the scraper process")
@click.option("--remote", "-r", is_flag=True, help="Denotes whether or not the scraper is accessing the database remotely (using {0} instead of {1})".format(DB_Controller.REMOTE_DB_CFG_NAME, DB_Controller.DB_CFG_NAME))
@click.option("--rows", is_flag=True, help="Gets a count of the rows currently stored in the database")
def main(start, quiet, stop, restart, status, overwrite, flair_scraper, pid, remote, rows):
    kwargs = {
        "start": start, "quiet": quiet, "stop": stop, "restart": restart, "status": status,
        "flair_scraper": flair_scraper, "pid": pid, "remote": remote, "rows": rows
    }

    RF1_Stats_Bot(**kwargs)


if __name__ == "__main__":
    main()
