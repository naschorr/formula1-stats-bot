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

## The flair_table.html is a prettified html file. (Prettifying not required?)
## It's made by hitting the 'edit' flair button, and then right-clicking 
## 'Inspect Source' on the 'select flair' bar. In the elements panel the next
## line down should be the div containing the flair selector 
## (class="flairoptionpane"). Right-click > Copy > OuterHTML, and then paste 
## into an empty html document in the text editor. The html is then 
## prettified using the 'HTML/CSS/JS Prettify' package for Sublime Text (3?)
## and saved.
FLAIR_TABLE_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, FLAIR_TABLE_NAME])
FLAIR_FILE_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, FLAIR_FILE])


class FlairTableParser(HTMLParser):
    def __init__(self):
        super(FlairTableParser, self).__init__()
        self.get_flair_data = False
        self.flairs = set()

    def handle_starttag(self, tag, attrs):
        if("span" == tag):
            for pair in attrs:
                if("class" == pair[0] and "flair" in pair[1]):
                    if(not any([flair_class if flair_class in pair[1] else False for flair_class in ["flair-label", "flair-empty"]])):
                        self.get_flair_data = True

    def handle_endtag(self, tag):
        if("span" == tag):
            self.get_flair_data = False


    def handle_data(self, data):
        if(self.get_flair_data):
            self.flairs.add(data)


def read_flair_table(flair_table_path, callback):
    for line in open(flair_table_path, "r"):
        callback(line)


def save_flair_json(flair_json_path, flairs, overwrite=False, **kwargs):
    if(os.path.isfile(flair_json_path) and not overwrite):
        raise RuntimeError("Can't overwrite {0} without the [--overwrite|-o] flag set.".format(flair_json_path))
        return

    with open(flair_json_path, "w") as flair_file:
        json.dump({FLAIR: flairs}, flair_file, **kwargs)


@click.command()
@click.option("--overwrite", "-o", is_flag=True, help="Overwrites any existing files when outputting {0}".format(FLAIR_FILE))
def main(overwrite):
    parser = FlairTableParser()
    read_flair_table(FLAIR_TABLE_PATH, parser.feed)
    flairs = sorted(parser.flairs)

    try:
        json_dumps_kwargs = {"indent": 4, "ensure_ascii": False}
        save_flair_json(FLAIR_FILE_PATH, flairs, overwrite, **json_dumps_kwargs)
    except Exception as e:
        print("Exception while saving {0} to {1}:\n".format(FLAIR_FILE, FLAIR_FILE_PATH), e)
        return
    else:
        print(FLAIR_FILE, "output:")
        print(json.dumps({FLAIR: flairs}, **json_dumps_kwargs))


if __name__ == '__main__':
    main()