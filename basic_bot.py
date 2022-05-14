from pathlib import Path

import hikari
import tanjun
import yuyo

from utils import yuyo_utils
from utils.config import Config


def create_bot() -> hikari.GatewayBot:
    """Creates the bot."""
    bot = hikari.GatewayBot(Config.bot_token, intents=hikari.Intents.NONE)

    component_client = yuyo.ComponentClient.from_gateway_bot(bot).set_constant_id(
        yuyo_utils.DELETE_CUSTOM_ID,
        yuyo_utils.delete_button_callback,
        prefix_match=True
    )
    client = tanjun.Client.from_gateway_bot(bot, declare_global_commands=True)
    # Load all modules in the modules folder
    client.load_modules(*Path("modules").glob("*.py"))
    # Add a callback to do any asnyc initialization on startup
    client.add_client_callback(tanjun.ClientCallbackNames.STARTING, component_client.open)
    client.add_client_callback(tanjun.ClientCallbackNames.CLOSING, component_client.close)
    client.set_type_dependency(yuyo.ComponentClient, component_client)
    return bot


if __name__ == "__main__":
    create_bot().run()
