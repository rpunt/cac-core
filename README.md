# CAC Core

An API client library providing essential functionality for command-line applications.

## Overview

CAC Core (`cac-core`) is a Python library that provides common utilities for building robust command-line applications. It includes modules for commands, configuration management, standardized logging, data modeling, and formatted output display.

## Features

- **Command**: Define commands, required or optional arguments, and action implementations
- **Configuration Management**: Load/save configs from YAML files with environment variable support
- **Standardized Logging**: Consistent, configurable logging across applications
- **Data Modeling**: Dynamic attribute creation and manipulation with dictionary-like access
- **Output Formatting**: Display data as tables or JSON with customization options

## Installation

```bash
# Install from PyPI
pip install cac-core

# Or install with Poetry
poetry add cac-core
```

## Usage

### Command

```python
import cac_core as cac

# Create a command class
class HelloCommand(cac.command.Command):
    def define_arguments(self, parser):
        """Define command arguments"""
        parser.add_argument('--name', default='World',
                          help='Name to greet')

    def execute(self, args):
        """Execute the command with parsed arguments"""
        logger = cac.logger.new(__name__)
        logger.info(f"Hello, {args.name}!")
        return f"Hello, {args.name}!"

# Use the command in your application
if __name__ == "__main__":
    # Create argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Demo application')

    # Initialize command
    cmd = HelloCommand()

    # Add command arguments
    cmd.define_arguments(parser)

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    result = cmd.execute(args)

    # Display result
    print(result)
```

### Configuration

```python
import cac_core as cac

# Load configuration
config = cac.config.Config("myapp")
server_url = config.get("server", "default-value")

# Update configuration
config.set("api_key", "my-secret-key")
config.save()
```

### Logging

```python
import cac_core as cac

# Create a logger
logger = cac.logger.new(__name__)
logger.info("Application started")
logger.debug("Debug information")
```

### Data Models

```python
import cac_core as cac

# Create data model
data = {
    "name": "Project X",
    "status": "active",
    "metadata": {
        "created": "2025-01-01",
        "version": "1.0"
    }
}

model = cac.model.Model(data)
print(model.name)  # "Project X"
print(model.metadata.version)  # "1.0"
```

### Output Formatting

```python
import cac_core as cac

# Create output handler
output = cac.output.Output({"output": "table"})

# Display data as table
models = [model1, model2, model3]
output.print_models(models)

# Display as JSON
output = cac.output.Output({"output": "json"})
output.print_models(models)
```

## Development

```bash
# Clone the repository
git clone https://github.com/rpunt/cac_core.git
cd cac_core

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

## Project Structure

- command.py - Command management
- config.py - Configuration management
- logger.py - Standardized logging
- model.py - Data modeling utilities
- output.py - Output formatting

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
