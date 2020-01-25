import json
from pathlib import Path

from click.testing import CliRunner

from oasapi.cli import validate, shorten_text, main, prune


def test_shorten_text():
    assert shorten_text("this is a long string", before=5, after=5) == "this ...tring"
    assert shorten_text("this is a long string", before=5, after=10) == "this ...ong string"
    assert shorten_text("this is a long string", before=10, after=5) == "this is a ...tring"
    assert shorten_text("this is a long string", before=10, after=10) == "this is a long string"


def test_main():
    runner = CliRunner()
    result = runner.invoke(main)

    assert (
        result.output
        == """Usage: main [OPTIONS] COMMAND [ARGS]...

  These are common operations offered by the oasapi library

Options:
  --help  Show this message and exit.

Commands:
  prune     Prune unused global definitions/responses/parameters, unused...
  validate  Validate the SWAGGER file.
"""
    )
    assert result.exit_code == 0


def test_validate_help():
    runner = CliRunner()
    result = runner.invoke(validate, ["--help"])

    assert (
        result.output
        == """Usage: validate [OPTIONS] SWAGGER

  Validate the SWAGGER file.

  SWAGGER is the path to the swagger file, in json or yaml format. It can be a
  file path, an URL or a dash (-) for the stdin

Options:
  -v, --verbose  Make the operation more talkative
  --help         Show this message and exit.
"""
    )
    assert result.exit_code == 0


def test_prune_help():
    runner = CliRunner()
    result = runner.invoke(prune, ["--help"])
    print(result.output)
    assert (
        result.output
        == """Usage: prune [OPTIONS] SWAGGER

  Prune unused global definitions/responses/parameters, unused
  securityDefinition/scopes and unused tags from the swagger.

  SWAGGER is the path to the swagger file, in json or yaml format. It can be a
  file path, an URL or a dash (-) for the stdin

Options:
  -o, --output FILENAME  Path to write the pruned swagger
  -v, --verbose          Make the operation more talkative
  --help                 Show this message and exit.
"""
    )
    assert result.exit_code == 0


def test_validate_ok_file():
    runner = CliRunner()
    swagger_path = Path(__file__).parent.parent / "docs" / "samples" / "swagger_petstore.json"
    result = runner.invoke(validate, [str(swagger_path)])

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_validate_ok_url():
    runner = CliRunner()
    result = runner.invoke(validate, ["http://petstore.swagger.io/v2/swagger.json"])

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_validate_nok_notexistant_url():
    runner = CliRunner()
    result = runner.invoke(validate, ["http://petstore.swagger.io/v2/swagger.jso"])

    assert (
        result.output
        == "Error: Error when downloading http://petstore.swagger.io/v2/swagger.jso : Not Found (404)\n"
    )
    assert result.exit_code == 1


def test_validate_ok_stdin():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-", "-v"], input=json.dumps(swagger))

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_validate_nok_stdin_bad_json():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-"], input=json.dumps(swagger)[:-1])

    assert (
        result.output
        == """Error: Could not parse json/yaml swagger from '[stdin]' with content {"swagger": "2....": "v1.0"}\n"""
    )
    assert result.exit_code == 1


def test_validate_nok_stdin_bad_yaml():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-"], input=json.dumps(swagger)[1:])

    assert (
        result.output
        == """Error: Could not parse json/yaml swagger from '[stdin]' with content "swagger": "2.0...: "v1.0"}}\n"""
    )
    assert result.exit_code == 1


def test_validate_nok():
    runner = CliRunner()
    swagger_path = (
        Path(__file__).parent.parent / "docs" / "samples" / "swagger_petstore_with_errors.json"
    )
    result = runner.invoke(validate, [str(swagger_path)])

    assert result.output == (
        "The swagger is not valid. Following 6 errors have been detected:\n"
        "- Duplicate operationId @ 'paths./pet/findByStatus.get.operationId' "
        "-> the operationId 'updatePet' is already used in an endpoint.\n"
        "- Json schema validator error @ 'info' -> 'notvalidinfo' does not match any of the regexes: '^x-'\n"
        "- Json schema validator error @ 'paths./pet.post' -> 'responses' is a required property\n"
        "- Json schema validator error @ 'paths./pet/findByStatus.get.security.0.petstore_auth' -> 1 is not of type 'array'\n"
        "- Json schema validator error @ 'schemes.1' -> 'ftp' is not one of ['http', 'https', 'ws', 'wss']\n"
        "- Security scope not found @ 'paths./pet.put.security.[0].petstore_auth.think:pets' -> "
        "scope think:pets is not declared in the scopes of the securityDefinitions 'petstore_auth'\n"
    )
    assert result.exit_code == 1


def test_validate_nofile():
    runner = CliRunner()
    result = runner.invoke(validate, [])

    assert result.exit_code == 2


def test_prune_no_pruning_stdin():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(prune, ["-", "-v"], input=json.dumps(swagger))

    assert result.output == "The swagger had no unused elements.\n"
    assert result.exit_code == 0


def test_prune_ok_stdin():
    runner = CliRunner()
    swagger = dict(
        swagger="2.0",
        paths={},
        info=dict(title="my API", version="v1.0"),
        definitions={"unused": {}},
    )
    result = runner.invoke(prune, ["-", "-v"], input=json.dumps(swagger))

    assert (
        result.output
        == """The swagger has been pruned of 1 elements:
- Reference filtered out @ 'definitions.unused' -> reference not used
"""
    )
    assert result.exit_code == 0


def test_prune_nok_swagger_invalid():
    runner = CliRunner()
    swagger_path = (
        Path(__file__).parent.parent / "docs" / "samples" / "swagger_petstore_with_errors.json"
    )
    result = runner.invoke(prune, [str(swagger_path)])

    assert result.output == (
        "The swagger could not been pruned as it is invalid. Please ensure the "
        "swagger is valid before pruning it.\n"
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
