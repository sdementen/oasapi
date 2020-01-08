from pathlib import Path

from click.testing import CliRunner

from oasapi.cli import validate


def test_validate_ok():
    runner = CliRunner()
    swagger_path = Path(__file__).parent.parent / "docs" / "samples" / "swagger_petstore.json"
    result = runner.invoke(validate, [str(swagger_path)])

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


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
