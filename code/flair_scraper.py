from __future__ import print_function

from utilities import Utilities

import os
import sys
import json
import time
import click
if (sys.version_info[0] >= 3):
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser

from db_controller import DB_Controller


class FlairTableParser(HTMLParser):
    def __init__(self):
        try:
            super(FlairTableParser, self).__init__()
        except TypeError:
            HTMLParser.__init__(self)  # Python 2 old style classes http://stackoverflow.com/a/11527947
        self.inside_flair_option_pane = False
        self.inside_flair_span = False
        self.flairs = set()

    ## Overridden Methods

    def handle_starttag(self, tag, attrs):
        ## Make sure we're parsing the flair table
        if("div" == tag and self.is_value_in_tuple_list("flairoptionpane", attrs)):
            self.inside_flair_option_pane = True
            return

        ## Don't bother with non-span tags, or if we're not inside the flair
        ##  option pane.
        if("span" != tag or not self.inside_flair_option_pane):
            return

        ## Look through all HTMLParser attr pairs, and only enable the
        ## inside_flair_span flag if pair's name is "class", and the value
        ## has "flair" in it but not "flair-lable" or "flair-empty".
        for pair in attrs:
            if("class" == pair[0]): # and "flair" in pair[1]):
                classes = pair[1].split()
                if("flair" in classes and 
                    not any(flair_class in classes for flair_class in ["flair-label", "flair-empty"])):
                    self.inside_flair_span = True


    def handle_endtag(self, tag):
        ## Clear the flags
        if("div" == tag and self.inside_flair_option_pane):
            self.inside_flair_option_pane = False

        if("span" == tag and self.inside_flair_span):
            self.inside_flair_span = False


    def handle_data(self, data):
        ## The data in a qualifying span is the flair, so add it into the set
        if(self.inside_flair_span):
            self.flairs.add(data)

    ## Methods

    def is_value_in_tuple_list(self, value, tuple_list):
        for t in tuple_list:
            for item in t:
                if(value in item):
                    return True

        return False


class FlairScraper:
    ## Globals
    FLAIRS = "flairs"
    FLAIR_TABLE_NAME = "flair_table.html"
    FLAIR_JSON_NAME = "flairs.json"
    FLAIR_URL_SOURCE = "https://www.reddit.com/r/formula1/"
    REDDIT_CFG_NAME = "reddit.json"
    REDDIT_CFG_PATH = Utilities.build_path_from_config(REDDIT_CFG_NAME)
    EDIT_FLAIR_BTN_SELECTOR = "a.flairselectbtn.access-required"

    ## The flair_table.html is a prettified html file. (Prettifying not required?)
    ## It's made by hitting the 'edit' flair button, and then right-clicking 
    ## 'Inspect Source' on the 'select flair' bar. In the elements panel the next
    ## line down should be the div containing the flair selector 
    ## (class="flairoptionpane"). Right-click > Copy > OuterHTML, and then paste 
    ## into an empty html document in the text editor. The html is then 
    ## prettified using the 'HTML/CSS/JS Prettify' package for Sublime Text (3?)
    ## and saved.
    FLAIR_TABLE_PATH = Utilities.build_path_from_config(FLAIR_TABLE_NAME)
    FLAIR_JSON_PATH = Utilities.build_path_from_config(FLAIR_JSON_NAME)

    ## Flairs Table Config
    FLAIRS_TABLE = "flairs"
    FLAIRS_COLUMNS = ["flair"]

    ## Flairs table creation:
    """
    CREATE TABLE flairs (
        flair text PRIMARY KEY NOT NULL
    );
    """

    def __init__(self, **kwargs):
        ## Alias FlairScraper into 'static'. Just a bit less typing
        self.static = FlairScraper

        ## Handle the args
        self.overwrite = kwargs.get("overwrite")

        ## Init the parser and db
        parser = FlairTableParser()
        self.db = DB_Controller(**kwargs)

        ## Feed the open flair table containing html into the parser
        parser.feed(self.open_flair_editor_html(self.static.FLAIR_URL_SOURCE))

        ## Get a sorted list of the flairs
        self.flairs = sorted(parser.flairs)

        if(kwargs.get("json")):
            json_dumps_kwargs = {"indent": 4, "ensure_ascii": False}
            try:
                self.save_flair_json(self.static.FLAIR_JSON_PATH, self.overwrite, **json_dumps_kwargs)
            except Exception as e:
                print("Exception while saving {0} to {1}:\n".format(FlairScraper.FLAIR_JSON_NAME, self.static.FLAIR_JSON_PATH), e, flush=True)
                return
            else:
                ## If the save was successful, print the encoded json
                print(FlairScraper.FLAIR_JSON_NAME, "output:")
                print(json.dumps({self.static.FLAIRS: self.flairs}, **json_dumps_kwargs), flush=True)
        else:
            self.save_flair_db()


    ## Methods

    def open_flair_editor_html(self, url):
        from selenium import webdriver

        ## Load the Reddit credentials
        reddit_cfg = Utilities.load_json(self.static.REDDIT_CFG_PATH)

        ## Init the webdriver (make sure the driver is in your system PATH)
        ##  https://sites.google.com/a/chromium.org/chromedriver/downloads)
        driver = webdriver.Chrome()
        driver.get(url)

        ## Login to Reddit - http://stackoverflow.com/a/30662876
        form = driver.find_element_by_id("login_login-main")

        username = form.find_element_by_name("user")
        username.clear()
        username.send_keys(reddit_cfg["username"])

        password = form.find_element_by_name("passwd")
        password.clear()
        password.send_keys(reddit_cfg["password"])

        submit = form.find_element_by_xpath("//button[. = 'login']")
        submit.click()

        ## Wait for login
        time.sleep(2)

        ## Open the edit flair table
        driver.find_element_by_css_selector(self.static.EDIT_FLAIR_BTN_SELECTOR).click()

        ## Wait for flair table to open
        time.sleep(2)

        return driver.page_source


    def save_flair_json(self, flair_json_path, overwrite, **kwargs):
        if(os.path.isfile(flair_json_path) and not overwrite):
            raise RuntimeError("Can't overwrite {0} without the [--overwrite|-o] flag set.".format(flair_json_path))
            return

        with open(flair_json_path, "w") as flair_file:
            json.dump({self.static.FLAIRS: self.flairs}, flair_file, **kwargs)


    def save_flair_db(self):
        for flair in self.flairs:
            self.db.insert_row(self.static.FLAIRS_COLUMNS, [flair], self.static.FLAIRS_TABLE)


@click.command()
@click.option("--overwrite", "-o", is_flag=True, help="Overwrites any existing files when outputting {0}".format(FlairScraper.FLAIR_JSON_NAME))
@click.option("--json", is_flag=True, help="Saves scraped flairs into a json file rather than the database")
def main(overwrite, json):
    kwargs = {"overwrite": overwrite, "json":json}

    ## Init the flair scraper
    FlairScraper(**kwargs)


if __name__ == '__main__':
    main()
