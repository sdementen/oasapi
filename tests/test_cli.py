from click.testing import CliRunner

from oasapi.cli import validate


def test_validate_ok():
    runner = CliRunner()
    result = runner.invoke(validate, [r"swagger_petstore.json"])

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_validate_nofile():
    runner = CliRunner()
    result = runner.invoke(validate, [])

    assert result.exit_code == 2
