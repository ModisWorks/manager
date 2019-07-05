import importlib
import logging
import os
import discord

from modis import main
from modis.tools import data

from . import ui_embed

logger = logging.getLogger(__name__)

# TODO All of this fix up


async def activate_module(channel, module_name, activate):
    """
    Changes a modules activated/deactivated state for a server

    Args:
        channel: The channel to send the message to
        module_name: The name of the module to change state for
        activate: The activated/deactivated state of the module
    """

    server_id = channel.server.id

    _dir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    _dir_modules = "{}/../".format(_dir)
    if not os.path.isfile("{}/{}/_data.py".format(_dir_modules, module_name)):
        await main.client.send_typing(channel)
        embed = ui_embed.error(channel, "Error", "No module found named '{}'".format(module_name))
        await embed.send()
        return

    try:
        import_name = ".modules.{}.{}".format(module_name, "_data")
        module_data = importlib.import_module(import_name, "modis")

        # Don't try and deactivate this module (not that it would do anything)
        if module_data.modulename == "manager":
            await main.client.send_typing(channel)
            embed = ui_embed.error(channel, "Error", "I'm sorry, Dave. I'm afraid I can't do that.")
            await embed.send()
            return

        # This /should/ never happen if everything goes well
        if module_data.modulename not in data.cache["servers"][server_id]:
            await main.client.send_typing(channel)
            embed = ui_embed.error(channel, "Error",
                                   "No data found for module '{}'".format(module_data.modulename))
            await embed.send()
            return

        # Modify the module
        if "activated" in data.cache["servers"][server_id][module_data.modulename]:
            data.cache["servers"][server_id][module_data.modulename]["activated"] = activate
            # Write the data
            data.write()

            await main.client.send_typing(channel)
            embed = ui_embed.modify_module(channel, module_data.modulename, activate)
            await embed.send()
            return
        else:
            await main.client.send_typing(channel)
            embed = ui_embed.error(channel, "Error", "Can't deactivate module '{}'".format(module_data.modulename))
            await embed.send()
            return
    except Exception as e:
        logger.error("Could not modify module {}".format(module_name))
        logger.exception(e)


async def warn_user(channel, user):
    """
    Gives a user a warning, and bans them if they are over the maximum warnings

    Args:
        channel: The channel to send the warning message in
        user: The user to give the warning to
    """

    server_id = channel.server.id

    if "warnings_max" not in data.cache["servers"][server_id]["modules"]["manager"]:
        data.cache["servers"][server_id]["modules"]["manager"]["warnings_max"] = 3
    if "warnings" not in data.cache["servers"][server_id]["modules"]["manager"]:
        data.cache["servers"][server_id]["modules"]["manager"]["warnings"] = {}

    if user.id in data.cache["servers"][server_id]["modules"]["manager"]["warnings"]:
        data.cache["servers"][server_id]["modules"]["manager"]["warnings"][user.id] += 1
    else:
        data.cache["servers"][server_id]["modules"]["manager"]["warnings"][user.id] = 1

    data.write()

    warnings = data.cache["servers"][server_id]["modules"]["manager"]["warnings"][user.id]
    max_warnings = data.cache["servers"][server_id]["modules"]["manager"]["warnings_max"]

    await main.client.send_typing(channel)
    embed = ui_embed.user_warning(channel, user, warnings, max_warnings)
    await embed.send()

    if warnings >= max_warnings:
        await ban_user(channel, user)


async def ban_user(channel, user):
    """
    Bans a user from a server

    Args:
        channel: The channel to send the warning message in
        user: The user to give the warning to
    """

    server_id = channel.server.id

    # Set the user's warnings to 0
    if "warnings" in data.cache["servers"][server_id]["modules"]["manager"]:
        if user.id in data.cache["servers"][server_id]["manager"]["warnings"]:
            data.cache["servers"][server_id]["manager"]["warnings"][user.id] = 0
            data.write()

    try:
        await main.client.ban(user)
    except discord.errors.Forbidden:
        await main.client.send_typing(channel)
        embed = ui_embed.error(channel, "Ban Error", "I do not have the permissions to ban that person.")
        await embed.send()
        return

    await main.client.send_typing(channel)
    embed = ui_embed.user_ban(channel, user)
    await embed.send()

    try:
        response = "You have been banned from the server '{}' " \
                   "contact the owners to resolve this issue.".format(channel.server.name)
        await main.client.send_message(user, response)
    except Exception as e:
        logger.exception(e)


async def kick_user(channel, user):
    """
    Kick a user from a server

    Args:
        channel: The channel to send the warning message in
        user: The user to give the warning to
    """

    server_id = channel.server.id

    # Set the user's warnings to 0
    if "warnings" in data.cache["servers"][server_id]["modules"]["manager"]:
        if user.id in data.cache["servers"][server_id]["manager"]["warnings"]:
            data.cache["servers"][server_id]["manager"]["warnings"][user.id] = 0
            data.write()

    try:
        await main.client.kick(user)
    except discord.errors.Forbidden:
        await main.client.send_typing(channel)
        embed = ui_embed.error(channel, "Kick Error", "I do not have the permissions to kick that person.")
        await embed.send()
        return

    await main.client.send_typing(channel)
    embed = ui_embed.user_kick(channel, user)
    await embed.send()

    try:
        response = "You have been banned from the server '{}' " \
                   "contact the owners to resolve this issue.".format(channel.server.name)
        await main.client.send_message(user, response)
    except Exception as e:
        logger.exception(e)
