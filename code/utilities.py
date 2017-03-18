import os
import json

## Globals
CONFIG_FOLDER_NAME = "config"


class Utilities:
    ## Gets the path to the root directory of this project, which is the next folder up from this one
    @staticmethod
    def get_root_path(**kwargs):
        join = kwargs.get("join", True)

        root = os.path.realpath(__file__).split(os.path.sep)[:-2]

        if(join):
            return os.path.sep.join(root)
        else:
            return root


    ## Builds an OS friendly path made of the given path elements
    @staticmethod
    def build_path(*elements):
        return os.path.sep.join(elements)


    ## Builds a path from the project root through the given path elements
    @staticmethod
    def build_path_from_root(*elements, **kwargs):
        join = kwargs.get("join", True)

        root = Utilities.get_root_path(join=False)
        root.extend([element for element in elements])

        if(join):
            return os.path.sep.join(root)
        else:
            return root


    ## Builds a path from the project's config folder through the given path elements
    @staticmethod
    def build_path_from_config(*elements, **kwargs):
        join = kwargs.get("join", True)

        return Utilities.build_path_from_root(CONFIG_FOLDER_NAME, *elements, join=join)


    ## Loads the json from the given file
    @staticmethod
    def load_json(path):
        with open(path, "r") as fd:
            return json.load(fd)