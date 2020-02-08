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
from typing import List

import click
import yaml

import oasapi
from oasapi.filter import FilterCondition
from .common import CliOasapiCommand, SwaggerFileURL, validate_json_yaml_filename

commands = [
    CliOasapiCommand(
        name="prune",
        command=oasapi.prune,
        extra_options=[],
        action_messages=(
            "The swagger has been pruned of {len(actions)} elements:",
            "The swagger had no unused elements.",
        ),
        action_item="- {action.type} @ '{action.format_path(action.path)}' -> {action.reason}",
        description="Prune from the SWAGGER unused global definitions/responses/parameters, "
        "unused securityDefinition/scopes, unused tags and unused paths.",
    ),
    CliOasapiCommand(
        name="validate",
        command=oasapi.validate,
        extra_options=[],
        action_messages=(
            "The swagger is not valid. Following {len(actions)} errors have been detected:",
            "The swagger is valid.",
        ),
        action_item="- {action.type} @ '{action.format_path(action.path)}' -> {action.reason}",
        description="Validate the SWAGGER according to the specs.",
        action_results=(1, 0),
    ),
    CliOasapiCommand(
        name="filter",
        command=lambda swagger, tag, path, security_scope: oasapi.filter(
            swagger,
            mode="keep_only",
            conditions=[
                FilterCondition(
                    tags=tag or None,
                    operations=path or None,
                    security_scopes=security_scope or None,
                )
            ],
        ),
        extra_options=[
            click.option("-t", "--tag", help="A tag to keep", multiple=True),
            click.option("-p", "--path", help="A path to keep", multiple=True),
            click.option("-sc", "--security-scope", help="A security scope to keep", multiple=True),
        ],
        action_messages=(
            "The swagger has filtered or removed the following {len(actions)} operations:",
            "The swagger is unchanged after filtering.",
        ),
        action_item="- {action.type} @ '{action.format_path(action.path)}' -> {action.reason}",
        description="Filter the SWAGGER operations based on tags, operation path or security scopes.",
    ),
]


@click.group()
def main():
    """These are common operations offered by the oasapi library"""


def create_commands(commands: List[CliOasapiCommand]):
    """Generate all the commands for the cli."""

    def create_command(command: CliOasapiCommand):
        def cmd(verbose, silent, **kwargs):
            if verbose > 0:
                logging.basicConfig(level=logging.DEBUG)

            action_message, noaction_message = command.action_messages
            action_exit_code, noaction_exit_code = command.action_results

            # extract input/output
            swagger = kwargs.pop("swagger").swagger
            output = kwargs.pop("output", None)

            secho = click.secho if not silent else lambda *args, **kwargs: None

            try:
                swagger, actions = command.command(swagger, **kwargs)
            except Exception as e:
                # something wrong happened, check if due to invalid swagger
                _, validation_actions = oasapi.validate(swagger)
                if validation_actions:
                    secho(
                        f"Failed to '{command.name}' the swagger as it is invalid. "
                        f"Please ensure the swagger is valid before rerunning '{command.name}'.\n"
                        f"You can check for validity with the 'validate' command.",
                        fg="red",
                        err=True,
                    )
                else:  # pragma: no cover
                    # should not happen
                    secho(
                        f"Failed to '{command.name}' the swagger due to an unhandled exception ({e}). Please fill an issue.",
                        fg="red",
                        err=True,
                    )

                sys.exit(1)

            if output:
                if output.extension in {"yaml", "yml"}:
                    yaml.dump(swagger, output, sort_keys=False)
                elif output.extension in {"json"}:
                    output.write(json.dumps(swagger, indent=2))
                else:  # pragma: no cover
                    raise ValueError("extension of output could not be determined")

            if actions:
                # display message in case of actions as well as all actions
                # and exit with the action_exit_code
                secho(eval(f'f"{action_message}"'), fg="red", err=True)
                for action in sorted(actions, key=lambda error: str(error)):
                    secho(eval(f'f"{command.action_item}"'), fg="red", err=True)
                sys.exit(action_exit_code)
            else:
                # display message in case of no actions
                # and exit with the noaction_exit_code
                secho(noaction_message, fg="green", err=True)
                sys.exit(noaction_exit_code)

        cmd.__doc__ = command.description
        cmd.__doc__ += """

            SWAGGER is the path to the swagger file, in json or yaml format.
            It can be a file path, an URL or a dash (-) for the stdin"""

        decorators = [
            main.command(name=command.name),
            click.option("-v", "--verbose", count=True, help="Make the operation more talkative"),
            click.option(
                "-s", "--silent", is_flag=True, help="Do not print the oasapi messages to stderr"
            ),
        ]
        decorators.append(
            click.argument("swagger", callback=SwaggerFileURL.open_url, metavar="SWAGGER")
        )
        decorators.append(
            click.option(
                "-o",
                "--output",
                help="Path to write the resulting swagger ('-' for stdout)",
                type=click.File("w"),
                callback=validate_json_yaml_filename,
            )
        )
        # add extra options
        decorators += command.extra_options

        for decorator in decorators:
            cmd = decorator(cmd)

        return cmd

    command_functions = {command.name: create_command(command) for command in commands}
    return command_functions


# create all commands and add them to the locals()
locals().update(create_commands(commands))
