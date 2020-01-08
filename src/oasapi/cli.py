"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -m oasapi` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``oasapi.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``oasapi.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import json
import sys
from pathlib import Path

import click
import yaml

import oasapi


@click.group()
def cli():
    pass


@cli.command(name="validate")
@click.argument('swagger', type=click.Path(exists=True, dir_okay=False, resolve_path=True, allow_dash=True))
def validate(swagger: str):
    """Validate the SWAGGER file.

    SWAGGER is the path to the swagger file, in json or yaml format."""
    file_content = Path(swagger).read_text()
    if file_content.startswith("{"):
        # this is a json file
        swagger = json.loads(file_content)
    else:
        # this is a yaml file
        swagger = yaml.safe_load(file_content)

    errors = oasapi.validate_swagger(swagger)
    if errors:
        # display error messages and exit with code = 1
        click.echo(click.style("The swagger is not valid. Following errors have been detected:", fg="red"))
        for error in sorted(errors,key=lambda error:str(error)):
            click.echo(click.style(f"- {error.type} @ '{error.format_path(error.path)}' -> {error.reason}", fg="red"))
        sys.exit(1)
    else:
        # informs everything OK
        click.echo(click.style("The swagger is valid.", fg="green"))
