from .cli import CLI
from .enums import RUN_MENU
from .models.genesys import ClientCredentials, BusinessUnit
from .models.config import Region
from questionary import Choice


class Prompts:
    def __init__(self, cli: CLI):
        self.cli = cli

    def welcome_message(self) -> None:
        self.cli.print_info("\nWelcome to the Genesys Activity Code Comparison")
        self.cli.print_info("-----------------------------------------------")

    def welcome_menu(self) -> RUN_MENU:
        choice = self.cli.select("Select : ", [RUN_MENU.START, RUN_MENU.QUIT])
        if choice is None:
            raise KeyboardInterrupt
        return RUN_MENU(choice)

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

        return ClientCredentials(
            client_id=client_id.strip(), client_secret=client_secret.strip()
        )

    def prompt_user_for_region(self, config: list[Region]) -> Region:
        region_list = [
            Choice(title=region.name, value=region.name) for region in config
        ]
        region_name = self.cli.select("Select region: ", region_list)
        if region_name is None:
            raise KeyboardInterrupt

        for region in config:
            if region.name == region_name:
                return region

        raise RuntimeError(f"Selected region was not found: {region_name}")

    def prompt_user_for_bus(self, full_bus: list[BusinessUnit]) -> list[BusinessUnit]:
        bu_list = [Choice(title=bu.name, value=bu.bu_id) for bu in full_bus]
        user_selected_bus = []
        while not user_selected_bus:
            user_selected_bus = self.cli.checkbox("Select BUs:", bu_list)

            if user_selected_bus is None:
                raise KeyboardInterrupt

            if not user_selected_bus:
                self.cli.print_warn(
                    "Please <space> to select and then <enter>. If you want to exit, press ctrl+c."
                )
        selected_ids = set(user_selected_bus)
        return [bu for bu in full_bus if bu.bu_id in selected_ids]
