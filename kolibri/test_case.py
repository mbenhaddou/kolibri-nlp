import logging
import os
import pathlib
import shutil
import tempfile
from unittest import TestCase


TEST_DIR = tempfile.mkdtemp(prefix="kolibri_tests")


class KolibriTestCase(TestCase):
    """
    A custom subclass of :class:`~unittest.TestCase` that disables some of the
    more verbose AllenNLP logging and that creates and destroys a temp directory
    as a test fixture.
    """

    PROJECT_ROOT = (pathlib.Path(__file__).parent / "..").resolve()
    MODULE_ROOT = PROJECT_ROOT / "kolibri"
    TESTS_ROOT = MODULE_ROOT / "tests"


    def setUp(self):
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.DEBUG
        )

        self.TEST_DIR = pathlib.Path(TEST_DIR)

        os.makedirs(self.TEST_DIR, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.TEST_DIR)
