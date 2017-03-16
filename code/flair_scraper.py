import os
import json
import click
from html.parser import HTMLParser

## Literals
FLAIR = "flair"

## Globals
CONFIG_FOLDER_NAME = "config"
FLAIR_TABLE_NAME = "flair_table.html"
FLAIR_FILE = "flairs.json"


class FlairTableParser(HTMLParser):
    def __init__(self):
        super(FlairTableParser, self).__init__()
        self.get_flair_data = False
        self.flairs = set()

    ## Overridden Methods

    def handle_starttag(self, tag, attrs):
        ## Don't bother with non-span tags
        if("span" != tag):
            return

        ## Look through all HTMLParser attr pairs, and only enable the
        ## get_flair_data flag if pair's name is "class", and the value
        ## has "flair" in it but not "flair-lable" or "flair-empty".
        for pair in attrs:
            if("class" == pair[0]): # and "flair" in pair[1]):
                classes = pair[1].split()
                if("flair" in classes and 
                    not any(flair_class in classes for flair_class in ["flair-label", "flair-empty"])):
                    self.get_flair_data = True


    def handle_endtag(self, tag):
        ## Clear the flag at the end of every span
        if("span" == tag):
            self.get_flair_data = False


    def handle_data(self, data):
        ## The data in a qualifying span is the flair, so add it into the set
        if(self.get_flair_data):
            self.flairs.add(data)


class FlairScraper:
    ## The flair_table.html is a prettified html file. (Prettifying not required?)
    ## It's made by hitting the 'edit' flair button, and then right-clicking 
    ## 'Inspect Source' on the 'select flair' bar. In the elements panel the next
    ## line down should be the div containing the flair selector 
    ## (class="flairoptionpane"). Right-click > Copy > OuterHTML, and then paste 
    ## into an empty html document in the text editor. The html is then 
    ## prettified using the 'HTML/CSS/JS Prettify' package for Sublime Text (3?)
    ## and saved.
    FLAIR_TABLE_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, FLAIR_TABLE_NAME])
    FLAIR_JSON_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, FLAIR_FILE])

    def __init__(self, **kwargs):
        ## Alias FlairScraper into 'static'. Just a bit less typing
        static = FlairScraper

        ## Handle the args
        self.overwrite = kwargs.get("overwrite")

        ## Init the parser and start reading data into it
        parser = FlairTableParser()
        self.read_flair_table(static.FLAIR_TABLE_PATH, parser.feed)
        
        ## Get a sorted list of the flairs
        self.flairs = sorted(parser.flairs)

        ## Try to save the flairs in a json file
        json_dumps_kwargs = {"indent": 4, "ensure_ascii": False}
        try:
            self.save_flair_json(static.FLAIR_JSON_PATH, self.overwrite, **json_dumps_kwargs)
        except Exception as e:
            print("Exception while saving {0} to {1}:\n".format(FLAIR_FILE, static.FLAIR_JSON_PATH), e)
            return
        else:
            ## If the save was successful, print the encoded json
            print(FLAIR_FILE, "output:")
            print(json.dumps({FLAIR: self.flairs}, **json_dumps_kwargs))

    ## Methods

    def read_flair_table(self, flair_table_path, callback):
        for line in open(flair_table_path, "r"):
            callback(line)


    def save_flair_json(self, flair_json_path, overwrite, **kwargs):
        if(os.path.isfile(flair_json_path) and not overwrite):
            raise RuntimeError("Can't overwrite {0} without the [--overwrite|-o] flag set.".format(flair_json_path))
            return

        with open(flair_json_path, "w") as flair_file:
            json.dump({FLAIR: self.flairs}, flair_file, **kwargs)


@click.command()
@click.option("--overwrite", "-o", is_flag=True, help="Overwrites any existing files when outputting {0}".format(FLAIR_FILE))
def main(overwrite):
    ## Init the flair scraper
    FlairScraper(overwrite=overwrite)


if __name__ == '__main__':
    main()