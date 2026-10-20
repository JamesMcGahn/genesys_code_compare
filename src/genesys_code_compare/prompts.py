from .cli import CLI
from .enums import RUN_MENU
from .models.genesys import ClientCredentials, BusinessUnit
from .models.config import Region


class Prompts:
    def __init__(self, cli: CLI):
        self.cli = cli

    def welcome_message(self) -> None:
        self.cli.print_info("\nWelcome to the Genesys Activity Code Comparison")
        self.cli.print_info("-----------------------------------------------")

    def welcome_menu(self) -> None:
        return self.cli.select("Select : ", [RUN_MENU.START, RUN_MENU.QUIT])

    def enter_client_id(self) -> str:
        return self.cli.text_input("Enter the Client ID: ")

    def enter_client_secret(self) -> str:
        return self.cli.password_input("Enter the Client Secret: ")

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

    def prompt_user_for_region(self, config: list[Region]):
        region_list = [region.name for region in config]
        region_name = self.cli.select("Select region: ", region_list)

        if region_name is None:
            raise KeyboardInterrupt

        for region in config:
            if region.name == region_name:
                return region

        raise RuntimeError(f"Selected region was not found: {region_name}")

    def prompt_user_for_bus(self, full_bus: list[BusinessUnit]):
        bu_list = [bu.name for bu in full_bus]
        selected_list = self.cli.checkbox("Select BUs:", bu_list)
        print(selected_list)
        return selected_list
