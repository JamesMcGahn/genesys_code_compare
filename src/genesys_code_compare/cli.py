import questionary


def welcome_message() -> None:
    questionary.print("\nWelcome to the Genesys Activity Code Comparison")
    questionary.print("-----------------------------------------------")


def enter_client_id() -> str:
    question = questionary.text("Enter the Client ID: ")

    return question.ask()


def enter_client_secret() -> str:
    question = questionary.password("Enter the Client Secret: ")
    return question.ask()


def select_region(regions: list[str]) -> str:
    question = questionary.select("Select region: ", regions)
    return question.ask()


def print_error(message: str) -> None:
    questionary.print(f"ERROR: {message}", style="bold fg:red")


def print_info(message: str) -> None:
    questionary.print(message)


def print_status(message: str) -> None:
    questionary.print(message, style="bold fg:cyan")
