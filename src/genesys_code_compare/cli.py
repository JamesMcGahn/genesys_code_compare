import questionary
from .enums import RUN_MENU
from .models.genesys import ClientCredentials


class CLI:

    def welcome_message(self) -> None:
        questionary.print("\nWelcome to the Genesys Activity Code Comparison")
        questionary.print("-----------------------------------------------")

    def print_error(self, message: str) -> None:
        questionary.print(f"ERROR: {message}", style="bold fg:red")

    def print_info(self, message: str) -> None:
        questionary.print(message)

    def print_status(self, message: str) -> None:
        questionary.print(message, style="bold fg:cyan")

    def welcome_menu(self) -> None:
        question = questionary.select("Select : ", [RUN_MENU.START, RUN_MENU.QUIT])
        return question.ask()

    def enter_client_id(self) -> str:
        question = questionary.text("Enter the Client ID: ")

        return question.ask()

    def enter_client_secret(self) -> str:
        question = questionary.password("Enter the Client Secret: ")
        return question.ask()

    def enter_client_credentials(self) -> ClientCredentials:
        client_id = ""
        client_secret = ""

        while not client_id:
            client_id = self.enter_client_id()
            if client_id is None:
                raise KeyboardInterrupt

        while not client_secret:
            client_secret = self.enter_client_secret()
            if client_secret is None:
                raise KeyboardInterrupt

        return ClientCredentials(client_id=client_id, client_secret=client_secret)

    def select_region(self, regions: list[str]) -> str:
        question = questionary.select("Select region: ", regions)
        return question.ask()
