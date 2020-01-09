import json
from pathlib import Path

from click.testing import CliRunner

from oasapi.cli import validate, shorten_text


def test_shorten_text():
    assert shorten_text("this is a long string", before=5, after=5) == "this ...tring"
    assert shorten_text("this is a long string", before=5, after=10) == "this ...ong string"
    assert shorten_text("this is a long string", before=10, after=5) == "this is a ...tring"
    assert shorten_text("this is a long string", before=10, after=10) == "this is a long string"


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


def test_validate_ok_stdin():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-"], input=json.dumps(swagger))

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_validate_nok_stdin():
    runner = CliRunner()
    swagger = dict(swagger="2.0", paths={}, info=dict(title="my API", version="v1.0"))
    result = runner.invoke(validate, ["-"], input=json.dumps(swagger)[:-1])

    assert (
        result.output
        == """Error: Could not parse json/yaml swagger from '[stdin]' with content {"swagger": "2....": "v1.0"}\n"""
    )
    assert result.exit_code == 1


def test_validate_nok():
    runner = CliRunner()
    swagger_path = (
        Path(__file__).parent.parent / "docs" / "samples" / "swagger_petstore_with_errors.json"
    )
    result = runner.invoke(validate, [str(swagger_path)])

    assert result.output == (
        "The swagger is not valid. Following errors have been detected:\n"
        "- Duplicate operationId @ '$['paths']['/pet/findByStatus']['get']' "
        "-> the operationId 'updatePet' is already used in an endpoint\n"
        "- Json schema validator error @ '$['info']' -> 'notvalidinfo' does not match any of the regexes: '^x-'\n"
        "- Json schema validator error @ '$['paths']['/pet']['post']' -> 'responses' is a required property\n"
        "- Json schema validator error @ '$['schemes'][1]' -> 'ftp' is not one of ['http', 'https', 'ws', 'wss']\n"
        "- Security scope not found @ '$['paths']['/pet']['put']['security']['petstore_auth']['think:pets']' "
        "-> scope think:pets is not declared in the scopes of the securityDefinitions 'petstore_auth'\n"
    )
    assert result.exit_code == 1


def test_validate_nofile():
    runner = CliRunner()
    result = runner.invoke(validate, [])

    assert result.exit_code == 2
