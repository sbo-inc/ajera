import click


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def cli() -> None:
    pass


if __name__ == "__main__":
    cli()
