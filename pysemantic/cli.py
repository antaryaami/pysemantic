#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""semantic

Usage:
    semantic list
    semantic add PROJECT_NAME PROJECT_SPECFILE
    semantic remove PROJECT_NAME
    semantic set-schema PROJECT_NAME SCHEMA_FPATH

Options:
    -h --help	Show this screen
"""

from docopt import docopt
import project as pr
from errors import MissingProject
import os.path as op


def cli(arguments):
    """cli - The main CLI argument parser

    :param arguments: command line arguments
    """
    if arguments.get("list", False):
        pr.view_projects()
    elif arguments.get("add", False):
        proj_name = arguments.get("PROJECT_NAME")
        proj_spec = arguments.get("PROJECT_SPECFILE")
        proj_spec = op.abspath(proj_spec)
        pr.add_project(proj_name, proj_spec)
    elif arguments.get("remove", False):
        proj_name = arguments.get("PROJECT_NAME")
        if not pr.remove_project(proj_name):
            print "Removing the project {0} failed.".format(proj_name)
    elif arguments.get("set-schema", False):
        try:
            proj_name = arguments.get("PROJECT_NAME")
            proj_spec = arguments.get("SCHEMA_FPATH")
            proj_spec = op.abspath(proj_spec)
            pr.set_schema_fpath(proj_name, proj_spec)
        except MissingProject:
            msg = """Project {} not found in the configuration. Please use
            $ semantic add
            to register the project.""".format(arguments.get("PROJECT_NAME"))
            print msg


def main():
    arguments = docopt(__doc__, version="semantic v0.0.1")
    cli(arguments)
