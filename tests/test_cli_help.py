from click.testing import CliRunner

from qf_downloader.cli import cli


def test_cli_help_exits_zero() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
