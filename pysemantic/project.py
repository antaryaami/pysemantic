#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""
The Project class
"""

import os.path as op
import os
import pprint
from ConfigParser import RawConfigParser
from validator import SchemaValidator
import yaml
import pandas as pd

CONF_FILE_NAME = os.environ.get("PYSEMANTIC_CONFIG", "pysemantic.conf")


def _locate_config_file():
    """_locate_config_file: locates the configuration file used by semantic."""
    paths = [op.join(os.getcwd(), CONF_FILE_NAME),
             op.join(op.expanduser('~'), CONF_FILE_NAME)]
    for path in paths:
        if op.exists(path):
            return path


def _get_default_specfile(project_name):
    """_get_default_data_dictionary

    Returns the specifications file used by the given project. The
    configuration file is searched for first in the current directory and then
    in the home directory.

    :param project_name: Name of the project for which to get the spcfile.
    """
    path = _locate_config_file()
    parser = RawConfigParser()
    parser.read(path)
    return parser.get(project_name, 'specfile')


def add_project(project_name, specfile):
    """ Add a project to the global configuration file.

    :param project_name: Name of the project
    :param specfile: path to the data dictionary used by the project.
    """
    path = _locate_config_file()
    parser = RawConfigParser()
    parser.read(path)
    parser.add_section(project_name)
    parser.set(project_name, "specfile", specfile)
    with open(path, "w") as f:
        parser.write(f)


def view_projects():
    """View a list of all projects currently registered with pysemantic."""
    path = _locate_config_file()
    parser = RawConfigParser()
    parser.read(path)
    for section in parser.sections():
        project_name = section
        specfile = parser.get(section, "specfile")
        print "Project {0} with specfile at {1}".format(project_name, specfile)


def remove_project(project_name):
    """Remove a project from the global configuration file.

    :param project_name: Name of the project to remove.
    Returns true if the project existed.
    """
    path = _locate_config_file()
    parser = RawConfigParser()
    parser.read(path)
    result = parser.remove_section(project_name)
    if result:
        with open(path, "w") as f:
            parser.write(f)
    return result


class Project(object):

    def __init__(self, project_name, parser=None):
        """__init__

        :param project_name: Name of the project as specified in the pysemantic
        configuration file.
        :param parser: The parser to be used for reading dataset files. The
        default is `pandas.read_table`.
        """
        self.project_name = project_name
        self.specfile = _get_default_specfile(self.project_name)
        self.validators = {}
        if parser is not None:
            self.user_specified_parser = True
        else:
            self.user_specified_parser = False
        self.parser = parser
        with open(self.specfile, 'r') as f:
            specifications = yaml.load(f, Loader=yaml.CLoader)
        for name, specs in specifications.iteritems():
            self.validators[name] = SchemaValidator(specification=specs,
                                                    specfile=self.specfile,
                                                    name=name)

    def get_dataset_specs(self, dataset_name):
        """Returns the specifications for the specified dataset in the project.

        :param dataset_name: Name of the dataset
        """
        return self.validators[dataset_name].get_parser_args()

    def get_project_specs(self):
        """Returns a dictionary containing the schema for all datasets listed
        under this project."""
        specs = {}
        for name, validator in self.validators.iteritems():
            specs[name] = validator.get_parser_args()
        return specs

    def view_dataset_specs(self, dataset_name=None):
        """Pretty print the specifications for a dataset.

        :param dataset_name: Name of the dataset
        """
        specs = self.get_dataset_specs(dataset_name)
        pprint.pprint(specs)

    def set_dataset_specs(self, dataset_name, specs, write_to_file=False):
        """Sets the specifications to the dataset. Using this is not
        recommended. All specifications for datasets should be handled through
        the data dictionary.

        :param dataset_name: Name of the dataset for which specifications need
        to be modified.
        :param specs: A dictionary containing the new specifications for the
        dataset.
        :param write_to_file: If true, the data dictionary will be updated to
        the new specifications. If False (the default), the new specifications
        are used for the respective dataset only for the lifetime of the
        `Project` object.
        """
        validator = self.validators[dataset_name]
        return validator.set_parser_args(specs, write_to_file)

    def load_dataset(self, dataset_name):
        """Load and return the dataset.

        :param dataset_name: Name of the dataset
        """
        validator = self.validators[dataset_name]
        args = validator.get_parser_args()
        if isinstance(args, dict):
            self._update_parser(args)
            return self.parser(**args)
        else:
            dfs = []
            for argset in args:
                self._update_parser(argset)
                dfs.append(self.parser(**argset))
            return pd.concat(dfs, axis=0)

    def load_datasets(self):
        """Loads and returns all datasets listed in the data dictionary for the
        project."""
        datasets = {}
        for name in self.validators.iterkeys():
            datasets[name] = self.load_dataset(name)
        return datasets

    def _update_parser(self, argdict):
        if not self.user_specified_parser:
            sep = argdict['sep']
            if sep == ",":
                self.parser = pd.read_csv
            else:
                self.parser = pd.read_table
