#!/usr/bin/env python

"""
Command module for the Command and Control (CAC) Core package.

This module provides the Command class which serves as the base class for all
command implementations in the CAC framework. It defines the structure and
common functionality that all commands should implement.
"""

import abc
# import argparse
# import os
import logging


class Command(metaclass=abc.ABCMeta):
    """
    Abstract base class for all commands in the CAC framework.

    This class defines the interface that all command implementations must follow,
    with abstract methods for setting up parsers and executing commands. It also
    provides utility methods for output formatting.

    Attributes:
        log (Logger): Logger instance for the command
    """

    def __init__(self):
        """
        Initialize the command.
        """
        self.log = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def define_common_arguments(parser):
        """
        Defines common arguments for all command parsers.

        Args:
            parser (ArgumentParser): The argument parser to add arguments to
        """
        # placeholders for when we start inter-command communication
        # has_suppress = any(action.dest == 'suppress_output' for action in parser._actions)
        # if not has_suppress:
        #     parser.add_argument(
        #         "--suppress-output",
        #         help="Suppress output",
        #         action="store_true",
        #         default=False,
        #     )
        # has_external = any(action.dest == 'external_call' for action in parser._actions)
        # if not has_external:
        #     parser.add_argument(
        #         "--external-call",
        #         help="External call",
        #         action="store_true",
        #         default=False,
        #     )
        has_output = any(action.dest == 'output' for action in parser._actions)
        if not has_output:
            parser.add_argument(
                "--output",
                help="Output format",
                choices=["json", "table"],
                default="table",
                type=str,
                metavar="FORMAT",
            )

        # Check if the verbose argument already exists
        has_verbose = any(action.dest == 'verbose' for action in parser._actions)
        if not has_verbose:
            parser.add_argument(
                "--verbose",
                help="Verbose output",
                action="store_true",
                default=False
            )

    # # @abc.abstractmethod
    # def setup_parser(self, cls, parser):
    #     """
    #     Set up command-specific arguments for the parser.

    #     This abstract method must be implemented by all command subclasses.

    #     Args:
    #         parser (ArgumentParser): The argument parser to add arguments to
    #     """
    #     pass

    @abc.abstractmethod
    def execute(self, args):
        """
        Execute the command with the given arguments.

        This abstract method must be implemented by all command subclasses.

        Args:
            args (dict): Dictionary of parsed command-line arguments
        """
