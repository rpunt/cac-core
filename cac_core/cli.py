"""
CLI module for the Command and Control (CAC) Core package.

This module provides the CLI class which handles command-line interface
functionality, including argument parsing, command execution, and help text
generation. It serves as the main entry point for CAC command-line applications.
"""

import argparse
import sys

class CLI:
    """
    Command-line interface handler for CAC applications.

    This class parses command line arguments, loads command modules dynamically,
    executes commands, and generates help text. It supports extensible command
    hierarchies and customizable option parsing.

    Attributes:
        commands (dict): Dictionary mapping command names to their handler modules
        config (dict): Configuration settings for the CLI
        opts (dict): Runtime options parsed from command line arguments
    """

    def __init__(self, commands, config=None):
        self.commands = commands
        self.config = config or {}
        self.opts = {}
        self.parser = argparse.ArgumentParser(description=self.config.get('description', ''))

    def parse_args(self, args=None):
        """
        Parses command-line arguments.

        Args:
            args (list, optional): List of arguments to parse. Defaults to sys.argv[1:].

        Returns:
            dict: Parsed arguments as a dictionary.
        """
        self.opts = vars(self.parser.parse_args(args))
        return self.opts

    def execute(self):
        """
        Executes the command specified in the parsed arguments.
        """
        command = self.opts.get('command')
        if not command:
            self.parser.print_help()
            sys.exit(1)

        module = self.commands.get(command)
        if not module:
            print(f"Unknown command: {command}")
            sys.exit(1)

        module.execute(self.opts)
