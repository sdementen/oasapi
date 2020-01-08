from pathlib import Path

from click.testing import CliRunner

from oasapi.cli import validate


def test_validate_ok():
    runner = CliRunner()
    swagger_path = Path(__file__).parent / "swagger_petstore.json"
    result = runner.invoke(validate, [str(swagger_path)])

    assert result.output == "The swagger is valid.\n"
    assert result.exit_code == 0


def test_validate_nofile():
    runner = CliRunner()
    result = runner.invoke(validate, [])

    assert result.exit_code == 2
