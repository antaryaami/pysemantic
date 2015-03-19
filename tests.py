#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""
Tests
"""

import unittest
import yaml
import os.path as op
import os
import datetime
from copy import deepcopy
import numpy as np
from ConfigParser import RawConfigParser, NoSectionError
from validator import DataDictValidator
import project as pr

TEST_CONFIG_FILE_PATH = op.join(op.dirname(__file__), "testdata", "test.conf")
TEST_DATA_DICT = op.join(op.dirname(__file__), "testdata",
                                               "test_dictionary.yaml")


class TestProject(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # modify the testdata dict to have absolute paths
        with open(TEST_DATA_DICT, "r") as f:
            testData = yaml.load(f, Loader=yaml.CLoader)
        for name, specs in testData.iteritems():
            path = op.join(op.abspath(op.dirname(__file__)), specs['path'])
            specs['path'] = path
        with open(TEST_DATA_DICT, "w") as f:
            yaml.dump(testData, f, Dumper=yaml.CDumper,
                      default_flow_style=False)
        cls.data_specs = testData

        config_fname = op.basename(TEST_CONFIG_FILE_PATH)
        cls.test_conf_file = op.join(os.getcwd(), config_fname)
        with open(TEST_CONFIG_FILE_PATH, 'r') as f:
            confData = f.read()
        with open(cls.test_conf_file, 'w') as f:
            f.write(confData)
        pr.CONF_FILE_NAME = config_fname

    @classmethod
    def tearDownClass(cls):
        try:
            # modify the testdata back
            with open(TEST_DATA_DICT, "r") as f:
                testData = yaml.load(f, Loader=yaml.CLoader)
            testData['iris']['path'] = op.join("testdata", "iris.csv")
            testData['person_activity']['path'] = op.join("testdata",
                                                         "person_activity.tsv")
            with open(TEST_DATA_DICT, "w") as f:
                testData = yaml.dump(testData, f, Dumper=yaml.CDumper,
                                     default_flow_style=False)
        finally:
            os.unlink(cls.test_conf_file)

    def setUp(self):
        self.project = pr.Project(project_name="pysemantic")

    def test_add_project(self):
        """Test if adding a project works properly."""
        test_project_name = "test_project"
        pr.add_project(test_project_name, TEST_DATA_DICT)
        # Check if the project name is indeed present in the config file
        test_dict = pr._get_default_specfile(test_project_name)
        self.assertTrue(test_dict, TEST_DATA_DICT)

    def test_remove_project(self):
        """Test if removing a project works properly."""
        self.assertTrue(pr.remove_project("test_project"))
        self.assertRaises(NoSectionError, pr._get_default_specfile,
                          "test_project")

    def test_load_all(self):
        """Test if loading all datasets in a project works as expected."""
        loaded = self.project.load_datasets()
        self.assertItemsEqual(loaded.keys(), ('iris', 'person_activity'))

    def test_dataset_shape(self):
        """
        Test if the project object can load the dataset properly.
        """
        loaded = self.project.load_dataset("iris")
        spec_shape = (self.data_specs['iris']['nrows'],
                      self.data_specs['iris']['ncols'])
        self.assertItemsEqual(loaded.shape, spec_shape)
        loaded = self.project.load_dataset("person_activity")
        spec_shape = (self.data_specs['person_activity']['nrows'],
                      self.data_specs['person_activity']['ncols'])
        self.assertItemsEqual(loaded.shape, spec_shape)

    def test_dataset_colnames(self):
        """Check if the column names read by the loader are correct."""
        for name in ['iris', 'person_activity']:
            loaded = self.project.load_dataset(name)
            columns = loaded.columns.tolist()
            spec_colnames = self.data_specs[name]['dtypes'].keys()
            self.assertItemsEqual(spec_colnames, columns)

    def test_dataset_coltypes(self):
        """Check whether the columns have the correct datatypes."""
        for name in ['iris', 'person_activity']:
            loaded = self.project.load_dataset(name)
            for colname in loaded:
                if loaded[colname].dtype == np.dtype('O'):
                    self.assertEqual(self.data_specs[name]['dtypes'][colname],
                                     str)
                elif loaded[colname].dtype == np.dtype('<M8[ns]'):
                    self.assertEqual(self.data_specs[name]['dtypes'][colname],
                                     datetime.date)
                else:
                    self.assertEqual(loaded[colname].dtype,
                                     self.data_specs[name]['dtypes'][colname])


class TestConfig(unittest.TestCase):
    """
    Test the configuration management utilities.
    """

    @classmethod
    def setUpClass(cls):
        # Fix the relative paths in the config file.
        parser = RawConfigParser()
        parser.read(TEST_CONFIG_FILE_PATH)
        cls.old_fpath = parser.get("pysemantic", "specfile")
        parser.set("pysemantic", "specfile", op.abspath(cls.old_fpath))
        with open(TEST_CONFIG_FILE_PATH, "w") as f:
            parser.write(f)
        cls._parser = parser
        pr.CONF_FILE_NAME = "test.conf"

    @classmethod
    def tearDownClass(cls):
        cls._parser.set("pysemantic", "specfile", cls.old_fpath)
        with open(TEST_CONFIG_FILE_PATH, "w") as f:
            cls._parser.write(f)

    def setUp(self):
        self.testParser = RawConfigParser()
        for section in self._parser.sections():
            self.testParser.add_section(section)
            for item in self._parser.items(section):
                self.testParser.set(section, item[0], item[1])

    def test_config_loader_default_location(self):
        """Check if the config loader looks for the files in the correct
        places."""
        # Put the test config file in the current and home directories, with
        # some modifications.
        cwd_file = op.join(os.getcwd(), "test.conf")
        home_file = op.join(op.expanduser('~'), "test.conf")

        try:
            self.testParser.set("pysemantic", "specfile", os.getcwd())
            with open(cwd_file, "w") as f:
                self.testParser.write(f)
            specfile = pr._get_default_specfile("pysemantic")
            self.assertEqual(specfile, os.getcwd())

            os.unlink(cwd_file)

            self.testParser.set("pysemantic", "specfile", op.expanduser('~'))
            with open(home_file, "w") as f:
                self.testParser.write(f)
            specfile = pr._get_default_specfile("pysemantic")
            self.assertEqual(specfile, op.expanduser('~'))

        finally:
            os.unlink(home_file)


class TestDataDictValidator(unittest.TestCase):
    """
    Test the `pysemantic.validator.DataDictValidatorClass`
    """

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.specfile = "testdata/test_dictionary.yaml"
        with open(cls.specfile, "r") as f:
            cls._basespecs = yaml.load(f, Loader=yaml.CLoader)
        cls.basespecs = deepcopy(cls._basespecs)

        # fix the paths in basespecs if they aren't absolute
        for name, dataspec in cls.basespecs.iteritems():
            if not op.isabs(dataspec['path']):
                dataspec['path'] = op.abspath(dataspec['path'])
        # The updated values also need to be dumped into the yaml file, because
        # some functionality of the validator depends on parsing it.
        with open(cls.specfile, "w") as f:
            yaml.dump(cls.basespecs, f, Dumper=yaml.CDumper,
                      default_flow_style=False)

        cls.ideal_activity_parser_args = _get_person_activity_args()
        cls.ideal_iris_parser_args = _get_iris_args()

    @classmethod
    def tearDownClass(cls):
        with open(cls.specfile, "w") as f:
            yaml.dump(cls._basespecs, f, Dumper=yaml.CDumper,
                      default_flow_style=False)

    def assertKwargsEqual(self, dict1, dict2):
        self.assertEqual(len(dict1.keys()), len(dict2.keys()))
        for k, v in dict1.iteritems():
            self.assertIn(k, dict2)
            left = v
            right = dict2[k]
            if isinstance(left, (tuple, list)):
                self.assertItemsEqual(left, right)
            elif isinstance(left, dict):
                self.assertDictEqual(left, right)
            else:
                self.assertEqual(left, right)

    def assertKwargsEmpty(self, data):
        for value in data.itervalues():
            self.assertIn(value, ("", 0, 1, [], (), {}, None, False))

    def test_validator_with_specdict_iris(self):
        """Check if the validator works when only the specification is supplied
        as a dictionary for the iris dataset."""
        validator = DataDictValidator(specification=self.basespecs['iris'])
        validated_parser_args = validator.get_parser_args()
        self.assertKwargsEqual(validated_parser_args,
                               self.ideal_iris_parser_args)

    def test_validator_with_specdist_activity(self):
        """Check if the validator works when only the specification is supplied
        as a dictionary for the person activity dataset."""
        validator = DataDictValidator(
                               specification=self.basespecs['person_activity'])
        validated = validator.get_parser_args()
        self.assertKwargsEqual(validated, self.ideal_activity_parser_args)

    def test_error_for_relative_filepath(self):
        """Test if validator raises errors when relative paths are found in the
        dictionary."""
        specs = self.basespecs['iris']
        old_path = specs['path']
        try:
            specs['path'] = op.join("testdata", "iris.csv")
            validator = DataDictValidator(specifications=specs)
            self.assertEqual(validator.filepath, "")
        finally:
            specs['path'] = old_path

    def test_error_only_specfile(self):
        """Test if the validator fails when only the path to the specfile is
        provided. """
        validator = DataDictValidator(specfile=self.specfile)
        self.assertKwargsEmpty(validator.get_parser_args())

    def test_error_only_name(self):
        """Test if the validator fails when only the path to the specfile is
        provided. """
        validator = DataDictValidator(name="iris")
        self.assertKwargsEmpty(validator.get_parser_args())

    def test_validator_specfile_name_iris(self):
        """Test if the validator works when providing specifle and name for the
        iris dataset."""
        validator = DataDictValidator(specfile=self.specfile, name="iris")
        validated_parser_args = validator.get_parser_args()
        self.assertKwargsEqual(validated_parser_args,
                               self.ideal_iris_parser_args)

    def test_validator_specfile_name_activity(self):
        """Test if the validator works when providing specifle and name for the
        activity dataset."""
        validator = DataDictValidator(specfile=self.specfile,
                                      name="person_activity")
        validated_parser_args = validator.get_parser_args()
        self.assertKwargsEqual(validated_parser_args,
                               self.ideal_activity_parser_args)


def _get_iris_args():
    filepath = op.join(op.dirname(__file__), "testdata", "iris.csv")
    return dict(filepath_or_buffer=op.abspath(filepath),
                sep=",", nrows=150,
                dtype={'Petal Length': float,
                       'Petal Width': float,
                       'Sepal Length': float,
                       'Sepal Width': float,
                       'Species': str},
                usecols=['Petal Length', 'Sepal Length', 'Petal Width',
                         'Sepal Width', 'Species'])


def _get_person_activity_args():
    filepath = op.join(op.dirname(__file__), "testdata", "person_activity.tsv")
    return dict(filepath_or_buffer=op.abspath(filepath),
                sep="\t", nrows=100, dtype={'sequence_name': str,
                                            'tag': str,
                                            'x': float,
                                            'y': float,
                                            'z': float,
                                            'activity': str},
                usecols=['sequence_name', 'tag', 'date', 'x', 'y', 'z',
                         'activity'],
                parse_dates=['date'])


if __name__ == '__main__':
    unittest.main()
