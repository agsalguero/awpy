import json
import logging
import os
import re
import subprocess
import pandas as pd

from csgo.utils import NpEncoder, check_go_version


class DemoParser:
    """ This class can parse a CSGO demofile to various outputs, such as JSON or CSV. Accessible via csgo.parser import DemoParser

    Attributes:
        demofile (string) : A string denoting the path to the demo file, which ends in .dem
        log (boolean)     : A boolean denoting if a log will be written. If true, log is written to "csgo_parser.log"
        demo_id (string) : A unique demo name/game id. Default is inferred from demofile name
        parse_rate (int)  : One of 128, 64, 32, 16, 8, 4, 2, or 1. The lower the value, the more frames are collected. Indicates spacing between parsed demo frames in ticks. Default is 32.
    
    Raises:
        ValueError : Raises a ValueError if the Golang version is lower than 1.14
    """

    def __init__(self, demofile="", log=False, demo_id=None, parse_rate=None):
        # Set up logger
        if log:
            logging.basicConfig(
                filename="csgo_demoparser.log",
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            )
            self.logger = logging.getLogger("CSGODemoParser")
            self.logger.handlers = []
            fh = logging.FileHandler("csgo_demoparser.log")
            fh.setLevel(logging.INFO)
            self.logger.addHandler(fh)
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            )
            self.logger = logging.getLogger("CSGODemoParser")

        # Check if Golang is >= 1.14
        acceptable_go = check_go_version()
        if not acceptable_go:
            self.logger.error("Go version too low! Needs 1.14.0")
            raise ValueError("Go version too low! Needs 1.14.0")
        else:
            self.logger.info("Go version>=1.14.0")

        # Handle demofile and demo_id name. Finds right most '/' in case demofile is a specified path.
        self.demofile = demofile
        self.logger.info("Initialized CSGODemoParser with demofile " + self.demofile)
        if demo_id is None:
            self.demo_id = demofile[demofile.rfind("/") + 1 : -4]
        else:
            self.demo_id = demo_id
        self.logger.info("Setting demo id to " + self.demo_id)

        # Handle parse rate. Must be a power of 2^0 to 2^7. If not, then default to 2^5.
        if parse_rate is None:
            self.logger.warning("No parse rate set")
            self.parse_rate = 32
        elif parse_rate not in [1, 2, 4, 8, 16, 32, 64, 128]:
            self.logger.warning(
                "Parse rate of "
                + str(parse_rate)
                + " not acceptable! Parse rate must be between 2^0 and 2^7. Setting to DEFAULT value of 32."
            )
            self.parse_rate = 32
        else:
            self.parse_rate = parse_rate
        self.logger.info("Setting parse rate to " + str(self.parse_rate))

    def parse_demo(self):
        """ Parse a demofile using the Go script parse_demo.go -- this function takes no arguments, all arguments are set in initialization.

        Returns:
            Returns a dictionary...
        """
        path = os.path.join(os.path.dirname(__file__), "")
        self.logger.info("Running Golang parser from " + path)
        self.logger.info("Looking for file at " + os.getcwd() + "/" + self.demofile)
        proc = subprocess.Popen(
            [
                "go",
                "run",
                path + "/parse_demo.go",
                "-demo",
                os.getcwd() + "/" + self.demofile,
                "-parserate",
                str(self.parse_rate),
                "-demoid",
                str(self.demo_id),
            ],
            stdout=subprocess.PIPE,
        )
        if os.path.isfile(str(self.demo_id) + ".json"):
            self.logger.info(
                "Wrote demo parse output to " + str(self.demo_id) + ".json"
            )
        else:
            self.logger.error("No file produced, error in calling Golang")
