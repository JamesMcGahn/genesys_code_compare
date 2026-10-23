from .app import App


def main() -> None:
    app = App()
    try:

        app.run()
    except KeyboardInterrupt as e:
        app.cli.print_status("Exiting Application.")
        raise SystemExit(130) from e
    finally:
        app._http_session.close()
