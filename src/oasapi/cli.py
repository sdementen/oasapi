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
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

import click
import yaml
from attr import dataclass

import oasapi


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
    pass


@dataclass
class FileURL:
    url: str
    content: str

    @classmethod
    def open_url(cls, ctx, param, value):
        if value is not None:
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

            return cls(url=value, content=content)


@main.command(name="validate")
@click.argument("swagger_fileurl", callback=FileURL.open_url)
def validate(swagger_fileurl: FileURL):
    """Validate the SWAGGER file.

    SWAGGER is the path to the swagger file, in json or yaml format. It can be a file path, an URL or a dash (-) for the stdin"""
    file_content = swagger_fileurl.content
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
            f"Could not parse json/yaml swagger from '{swagger_fileurl.url}' with content {shorten_text(swagger_fileurl.content,15,10)}"
        )

    errors = oasapi.validate_swagger(swagger)
    if errors:
        # display error messages and exit with code = 1
        click.echo(
            click.style("The swagger is not valid. Following errors have been detected:", fg="red")
        )
        for error in sorted(errors, key=lambda error: str(error)):
            click.echo(
                click.style(
                    f"- {error.type} @ '{error.format_path(error.path)}' -> {error.reason}",
                    fg="red",
                )
            )
        sys.exit(1)
    else:
        # informs everything OK
        click.echo(click.style("The swagger is valid.", fg="green"))
