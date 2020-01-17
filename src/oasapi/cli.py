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
import logging
import sys
from typing import Dict
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

import click
import yaml
from attr import dataclass

import oasapi
from oasapi.timer import Timer


def shorten_text(txt, before, after, placeholder="..."):
    """Shorthen a text to max before+len(placeholder)+after chars.

    The new text will keep the before first characters and after last characters
    """
    # check if need to shorten
    if len(txt) <= before + len(placeholder) + after:
        # if not, return the original string
        return txt
    else:
        # otherwise, keep the beginning and end of sentence and insert the placeholder
        return txt[:before] + placeholder + txt[-after:]


@click.group()
def main():
    """These are common operations offered by the oasapi library"""


@dataclass
class FileURL:
    url: str
    content: str

    @classmethod
    def open_url(cls, ctx, param, value):
        try:
            # try to open as if value is an URL
            fp = urlopen(value)
        except HTTPError as err:
            raise click.ClickException(
                f"Error when downloading {value} : {err.reason} ({err.code})"
            )
        except (URLError, ValueError):
            # it should be a file
            path = click.File()
            fp = path.convert(value=value, param=param, ctx=ctx)
            if value == "-":
                value = "[stdin]"

        # read the file
        content = fp.read()

        # convert to text if bytes assuming utf-8
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        return FileURL(url=value, content=content)


@dataclass
class SwaggerFileURL(FileURL):
    swagger: Dict

    @classmethod
    def open_url(cls, ctx, param, value) -> "SwaggerFileURL":
        file_url = super().open_url(ctx, param, value)

        file_content = file_url.content
        if file_content.startswith("{"):
            # this is a json file
            try:
                swagger = json.loads(file_content)
            except json.JSONDecodeError:
                swagger = None
        else:
            # this is a yaml file
            try:
                swagger = yaml.safe_load(file_content)
            except yaml.YAMLError:
                swagger = None

        if swagger is None:
            raise click.ClickException(
                f"Could not parse json/yaml swagger from '{file_url.url}' "
                f"with content {shorten_text(file_url.content, 15, 10)}"
            )

        return cls(swagger=swagger, url=file_url.url, content=file_url.content)


@main.command(name="validate")
@click.argument("swagger_fileurl", callback=SwaggerFileURL.open_url, metavar="SWAGGER")
@click.option("-v", "--verbose", count=True, help="Make the operation more talkative")
def validate(swagger_fileurl: SwaggerFileURL, verbose):
    """Validate the SWAGGER file.

    SWAGGER is the path to the swagger file, in json or yaml format.
    It can be a file path, an URL or a dash (-) for the stdin"""
    if verbose > 0:
        logging.basicConfig(level=logging.DEBUG)

    swagger = swagger_fileurl.swagger

    with Timer("swagger validation"):
        errors = oasapi.validate(swagger)

    if errors:
        # display error messages and exit with code = 1
        click.secho(
            f"The swagger is not valid. Following {len(errors)} errors have been detected:",
            fg="red",
            err=True,
        )
        for error in sorted(errors, key=lambda error: str(error)):
            click.secho(
                f"- {error.type} @ '{error.format_path(error.path)}' -> {error.reason}",
                fg="red",
                err=True,
            )
        sys.exit(1)
    else:
        # informs everything OK
        click.secho("The swagger is valid.", fg="green", err=True)


@main.command(name="prune")
@click.argument("swagger_fileurl", callback=SwaggerFileURL.open_url, metavar="SWAGGER")
@click.option("-o", "--output", help="Path to write the pruned swagger", type=click.File("w"))
@click.option("-v", "--verbose", count=True, help="Make the operation more talkative")
def prune(swagger_fileurl: SwaggerFileURL, output, verbose):
    """Prune unused global definitions/responses/parameters, unused securityDefinition/scopes and unused tags from the swagger.

    SWAGGER is the path to the swagger file, in json or yaml format.
    It can be a file path, an URL or a dash (-) for the stdin"""
    if verbose > 0:
        logging.basicConfig(level=logging.DEBUG)

    swagger = swagger_fileurl.swagger

    with Timer("swagger pruning"):
        try:
            swagger, actions = oasapi.prune(swagger)
        except Exception as e:
            # something wrong happened, check if due to invalid swagger
            if oasapi.validate(swagger):
                click.secho(
                    f"The swagger could not been pruned as it is invalid. Please ensure the swagger is valid before pruning it.",
                    fg="red",
                    err=True,
                )
            else:  # pragma: no cover
                # should not happen
                click.secho(
                    f"The swagger could not been pruned due to an unhandled exception ({e}). Please fill an issue.",
                    fg="red",
                    err=True,
                )
            sys.exit(1)

    if output:
        output.write(json.dumps(swagger, indent=2))

    if actions:
        # display error messages and exit with code = 1
        click.secho(f"The swagger has been pruned of {len(actions)} elements:", fg="red", err=True)
        for action in sorted(actions, key=lambda error: str(error)):
            click.secho(
                f"- {action.type} @ '{action.format_path(action.path)}' -> {action.reason}",
                fg="red",
                err=True,
            )
    else:
        # informs everything OK
        click.secho("The swagger had no unused elements.", fg="green", err=True)
