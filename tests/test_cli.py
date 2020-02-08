import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from test_common import SWAGGER_SAMPLES_PATH

from oasapi.cli import main, validate, prune, filter
from oasapi.cli.common import shorten_text


def test_shorten_text():
    assert shorten_text("this is a long string", before=5, after=5) == "this ...tring"
    assert shorten_text("this is a long string", before=5, after=10) == "this ...ong string"
    assert shorten_text("this is a long string", before=10, after=5) == "this is a ...tring"
    assert shorten_text("this is a long string", before=10, after=10) == "this is a long string"


command_help_messages = [
    (
        main,
        """Usage: main [OPTIONS] COMMAND [ARGS]...

  These are common operations offered by the oasapi library

Options:
  --help  Show this message and exit.

Commands:
  filter    Filter the SWAGGER operations based on tags, operation path or...
  prune     Prune from the SWAGGER unused global...
  validate  Validate the SWAGGER according to the specs.
""",
    ),
    (
        validate,
        """Usage: validate [OPTIONS] SWAGGER

  Validate the SWAGGER according to the specs.

  SWAGGER is the path to the swagger file, in json or yaml format. It can be a
  file path, an URL or a dash (-) for the stdin

Options:
  -v, --verbose          Make the operation more talkative
  -s, --silent           Do not print the oasapi messages to stderr
  -o, --output FILENAME  Path to write the resulting swagger ('-' for stdout)
  --help                 Show this message and exit.
""",
    ),
    (
        prune,
        """Usage: prune [OPTIONS] SWAGGER

  Prune from the SWAGGER unused global definitions/responses/parameters,
  unused securityDefinition/scopes, unused tags and unused paths.

  SWAGGER is the path to the swagger file, in json or yaml format. It can be a
  file path, an URL or a dash (-) for the stdin

Options:
  -v, --verbose          Make the operation more talkative
  -s, --silent           Do not print the oasapi messages to stderr
  -o, --output FILENAME  Path to write the resulting swagger ('-' for stdout)
  --help                 Show this message and exit.
""",
    ),
    (
        filter,
        """Usage: filter [OPTIONS] SWAGGER

  Filter the SWAGGER operations based on tags, operation path or security
  scopes.

  SWAGGER is the path to the swagger file, in json or yaml format. It can be a
  file path, an URL or a dash (-) for the stdin

Options:
  -v, --verbose               Make the operation more talkative
  -s, --silent                Do not print the oasapi messages to stderr
  -o, --output FILENAME       Path to write the resulting swagger ('-' for
                              stdout)
  -t, --tag TEXT              A tag to keep
  -p, --path TEXT             A path to keep
  -sc, --security-scope TEXT  A security scope to keep
  --help                      Show this message and exit.
""",
    ),
]


@pytest.mark.parametrize("command,message", command_help_messages)
def test_help_messages(command, message):
    runner = CliRunner()
    result = runner.invoke(command, ["--help"])
    print(result.output)
    assert result.output == message
    assert result.exit_code == 0


command_ok_file = [
    (validate, "The swagger is valid.", 0),
    (prune, "The swagger had no unused elements.", 0),
    (filter, "The swagger is unchanged after filtering.", 0),
]
swaggers = [
    str(SWAGGER_SAMPLES_PATH / "swagger_petstore.json"),
    "http://petstore.swagger.io/v2/swagger.json",
]


@pytest.mark.parametrize("command,ok_message,ok_exit_code", command_ok_file)
@pytest.mark.parametrize("swagger", swaggers)
def test_command_ok_file(command, ok_message, ok_exit_code, swagger):
    runner = CliRunner()
    result = runner.invoke(command, [swagger])

    assert result.output == f"{ok_message}\n"
    assert result.exit_code == ok_exit_code


def test_command_nok_notexistant_url():
    runner = CliRunner()
    result = runner.invoke(validate, ["http://petstore.swagger.io/v2/swagger.jso"])

    assert (
        result.output
        == "Error: Error when downloading http://petstore.swagger.io/v2/swagger.jso : Not Found (404)\n"
    )
    assert result.exit_code == 1


def test_command_ok_stdin():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-", "-v"], input=json.dumps(swagger))

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_command_nok_stdin_bad_json():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-"], input=json.dumps(swagger)[:-1])

    assert (
        result.output
        == """Error: Could not parse json/yaml swagger from '[stdin]' with content {"swagger": "2....": "v1.0"}\n"""
    )
    assert result.exit_code == 1


def test_command_nok_stdin_bad_yaml():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-"], input=json.dumps(swagger)[1:])

    assert (
        result.output
        == """Error: Could not parse json/yaml swagger from '[stdin]' with content "swagger": "2.0...: "v1.0"}}\n"""
    )
    assert result.exit_code == 1


@pytest.mark.parametrize("command", [prune])
def test_command_invalid_swagger(command):
    runner = CliRunner()
    swagger_path = SWAGGER_SAMPLES_PATH / "swagger_petstore_with_errors.json"
    result = runner.invoke(command, [str(swagger_path)])

    assert result.output == (
        f"Failed to '{command.name}' the swagger as it is invalid. "
        f"Please ensure the swagger is valid before rerunning '{command.name}'.\n"
        f"You can check for validity with the 'validate' command.\n"
    )
    assert result.exit_code == 1


@pytest.mark.parametrize("command", [prune, validate, filter])
def test_command_nofile(command):
    runner = CliRunner()
    result = runner.invoke(command, [])

    assert result.exit_code == 2
    assert 'Error: Missing argument "SWAGGER".\n' in result.output


@pytest.mark.parametrize("verbose", [True, False])
@pytest.mark.parametrize("silent", [True, False])
def test_prune_no_pruning_stdin(verbose, silent):
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(
        prune,
        ["-"] + (["-s"] if silent else []) + (["-v"] if verbose else []),
        input=json.dumps(swagger),
    )

    assert result.output == ("The swagger had no unused elements.\n" if not silent else "")
    assert result.exit_code == 0


@pytest.mark.parametrize("verbose", [True, False])
def test_prune_ok_stdin(verbose):
    runner = CliRunner()
    swagger = dict(
        swagger="2.0",
        paths={},
        info=dict(title="my API", version="v1.0"),
        definitions={"unused": {}},
    )

    result = runner.invoke(prune, ["-"] + (["-v"] if verbose else []), input=json.dumps(swagger))

    assert (
        result.output
        == """The swagger has been pruned of 1 elements:
- Reference filtered out @ 'definitions.unused' -> reference not used
"""
    )
    assert result.exit_code == 0


def test_prune_nok_swagger_invalid():
    runner = CliRunner()
    swagger_path = SWAGGER_SAMPLES_PATH / "swagger_petstore_with_errors.json"
    result = runner.invoke(prune, [str(swagger_path)])

    assert result.output == (
        "Failed to 'prune' the swagger as it is invalid. Please ensure the swagger is "
        "valid before rerunning 'prune'.\n"
        "You can check for validity with the 'validate' command.\n"
    )
    assert result.exit_code == 1


def test_prune_output_swagger_stdin():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))

    file_output = "output.json"
    with runner.isolated_filesystem() as fld:
        fld = Path(fld)
        result = runner.invoke(prune, ["-", "-o", file_output], input=json.dumps(swagger))
        assert list(fld.iterdir()) == [fld / file_output]
        assert (Path(fld) / file_output).read_text() == json.dumps(swagger, indent=2)

    assert result.output == "The swagger had no unused elements.\n"
    assert result.exit_code == 0


def test_prune_output_swagger_yaml_order_kept():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))

    file_output = "output.yaml"
    with runner.isolated_filesystem() as fld:
        fld = Path(fld)
        result = runner.invoke(prune, ["-", "-o", file_output], input=json.dumps(swagger))
        assert list(fld.iterdir()) == [fld / file_output]
        assert (
            (Path(fld) / file_output).read_text()
            == """swagger: '2.0'
paths: {}
info:
  title: my API
  version: v1.0
"""
        )

    assert result.output == "The swagger had no unused elements.\n"
    assert result.exit_code == 0


def test_prune_output_bad_file_extension():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))

    file_output = "output.nonsense"
    with runner.isolated_filesystem() as fld:
        fld = Path(fld)
        result = runner.invoke(prune, ["-", "-o", file_output], input=json.dumps(swagger))

    print(result.output)
    print("xxx")
    print(result.output)

    assert (
        result.output
        == """Usage: prune [OPTIONS] SWAGGER

Error: Invalid value for "-o" / "--output": the extension of the file is 'nonsense' while it should be one of ['json', 'yaml', 'yml']
"""
    )
    assert result.exit_code == 2


@pytest.mark.parametrize("verbose", [True, False])
def test_filter_ok_file(verbose):
    runner = CliRunner()
    swagger_path = SWAGGER_SAMPLES_PATH / "swagger_petstore.json"
    result = runner.invoke(filter, [str(swagger_path), "-o", "-"] + (["-v"] if verbose else []))

    assert result.exit_code == 0


def test_filter_ok_file_empty():
    runner = CliRunner()
    swagger = dict(
        swagger="2.0",
        info=dict(title="my API", version="v1.0"),
        paths={"/foo": dict(get=dict(tags=["mytag", "othertag"]))},
    )

    file_output = "output.yaml"
    with runner.isolated_filesystem() as fld:
        fld = Path(fld)
        result = runner.invoke(
            filter, ["-", "-o", file_output, "-t", "mytag"], input=json.dumps(swagger)
        )
        assert list(fld.iterdir()) == [fld / file_output]
        assert (
            (Path(fld) / file_output).read_text()
            == """swagger: '2.0'
info:
  title: my API
  version: v1.0
paths:
  /foo:
    get:
      tags:
      - mytag
"""
        )

    print(result.output)
    assert (
        result.output
        == """The swagger has filtered or removed the following 1 operations:
- Operation was modified to match filters. @ 'paths./foo.get' -> The operation has been modified by a filter.
"""
    )
    assert result.exit_code == 0
