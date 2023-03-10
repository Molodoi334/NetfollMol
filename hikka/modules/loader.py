"""Loads and registers modules"""

# ÂŠī¸ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# đ https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# đ https://www.gnu.org/licenses/agpl-3.0.html
# Netfoll Team modifided Hikka files for Netfoll
# đ https://github.com/MXRRI/Netfoll

import ast
import asyncio
import contextlib
import copy
import functools
import importlib
import inspect
import logging
import os
import re
import shutil
import sys
import time
import typing
import uuid
from collections import ChainMap
from importlib.machinery import ModuleSpec
from urllib.parse import urlparse

import requests
import telethon
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Message

from .. import loader, main, utils
from .._local_storage import RemoteStorage
from ..compat import dragon, geek
from ..compat.pyroproxy import PyroProxyClient
from ..inline.types import InlineCall
from ..types import CoreOverwriteError, CoreUnloadError, DragonModule

logger = logging.getLogger(__name__)


class FakeLock:
    async def __aenter__(self, *args):
        pass

    async def __aexit__(self, *args):
        pass


class FakeNotifier:
    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass


@loader.tds
class LoaderMod(loader.Module):
    """Loads modules"""

    strings = {
        "name": "Loader",
        "repo_config_doc": "URL to a module repo",
        "avail_header": "đĸ <b>Modules from repo</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>â ī¸</emoji> <b>Please select a"
            " preset</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Preset not found</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Preset loaded</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Module not available"
            " in repo.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>File not found</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>â ī¸</emoji> <b>Provide a module to"
            " load</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Invalid Unicode"
            " formatting in module</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Loading failed. See"
            " logs for details</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>đ</emoji> <b>Module"
            "</b> <code>{}</code>{} <b>loaded {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>What class needs to be unloaded?</b>",
        "unloaded": "{} <b>Module {} unloaded.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Module not"
            " unloaded.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Requirements"
            " installation failed</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>đļ</emoji> <b>Requirements"
            " installation failed</b>\n<b>The most common reason is that Termux doesn't"
            " support many libraries. Don't report it as bug, this can't be solved.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>đ</emoji> <b>Installing"
            " requirements:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>đ</emoji> <b>Requirements"
            " installed, but a restart is required for</b> <code>{}</code> <b>to"
            " apply</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>All modules"
            " deleted</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>đ¤ˇââī¸</emoji> No docs",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>đ¤</emoji> <code>{}</code> {}"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>This module requires"
            " Netfoll inline feature and initialization of InlineManager"
            " failed</b>\n<i>Please, remove one of your old bots from @BotFather and"
            " restart userbot to load this module</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>This module requires"
            " Hikka {}+\nPlease, update with</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>This module requires"
            " FFMPEG, which is not installed</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>đĢļ</emoji> <b>Developer:</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>đĻ</emoji> <b>Dependencies:"
            "</b> \n{}"
        ),
        "by": "by",
        "module_fs": (
            "đŋ <b>Would you like to save this module to filesystem, so it won't get"
            " unloaded after restart?</b>"
        ),
        "save": "đŋ Save",
        "no_save": "đĢ Don't save",
        "save_for_all": "đŊ Always save to fs",
        "never_save": "đĢ Never save to fs",
        "will_save_fs": (
            "đŊ Now all modules, loaded with .loadmod will be saved to filesystem"
        ),
        "add_repo_config_doc": "Additional repos to load from",
        "share_link_doc": "Share module link in result message of .dlmod",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>đ</emoji> <b>Link:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>â ī¸</emoji> <b>Do not use `blob`"
            " links to download modules. Consider switching to `raw` instead</b>"
        ),
        "suggest_subscribe": (
            "\n\nâ­ī¸ <b>This module is"
            " made by {}. Do you want to join this channel to support developer?</b>"
        ),
        "subscribe": "đŦ Subscribe",
        "no_subscribe": "đĢ Don't subscribe",
        "subscribed": "đŦ Subscribed",
        "not_subscribed": "đĢ I will no longer suggest subscribing to this channel",
        "confirm_clearmodules": "â ī¸ <b>Are you sure you want to clear all modules?</b>",
        "clearmodules": "đ Clear modules",
        "cancel": "đĢ Cancel",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>This module"
            " attempted to override the core one (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Don't report it as bug."
            " It's a security measure to prevent replacing core modules with some"
            " junk</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>This module"
            " attempted to override the core command"
            " (</b><code>{}{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Don't report it as bug."
            " It's a security measure to prevent replacing core modules' commands with"
            " some junk</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>You can't unload"
            " core module</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Don't report it as bug."
            " It's a security measure to prevent replacing core modules with some"
            " junk</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>You can't unload"
            " library</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>đĢ</emoji> <b>Module"
            "</b> <code>{}</code> <b>requests permission to join channel <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">â</emoji> Reason: {}</b>\n\n<i>Waiting'
            ' for <a href="https://t.me/{}">approval</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>đ</emoji> <b>Installing module"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Repo</b>"
            " <code>{}</code> <b>is already added</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Repo</b>"
            " <code>{}</code> <b>added</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>You need to specify"
            " repo to add</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Repo</b>"
            " <code>{}</code> <b>is not added</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Repo</b>"
            " <code>{}</code> <b>deleted</b>"
        ),
    }

    strings_ru = {
        "repo_config_doc": "ĐĄŅŅĐģĐēĐ° Đ´ĐģŅ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ĐŧĐžĐ´ŅĐģĐĩĐš",
        "add_repo_config_doc": "ĐĐžĐŋĐžĐģĐŊĐ¸ŅĐĩĐģŅĐŊŅĐĩ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đ¸",
        "avail_header": "đĸ <b>ĐŅĐ¸ŅĐ¸Đ°ĐģŅĐŊŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸ Đ¸Đˇ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Ņ</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>â ī¸</emoji> <b>ĐŅĐąĐĩŅĐ¸ ĐŋŅĐĩŅĐĩŅ</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐŅĐĩŅĐĩŅ ĐŊĐĩ ĐŊĐ°ĐšĐ´ĐĩĐŊ</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>ĐŅĐĩŅĐĩŅ ĐˇĐ°ĐŗŅŅĐļĐĩĐŊ</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐžĐ´ŅĐģŅ ĐŊĐĩĐ´ĐžŅŅŅĐŋĐĩĐŊ Đ˛"
            " ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đ¸.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Đ¤Đ°ĐšĐģ ĐŊĐĩ ĐŊĐ°ĐšĐ´ĐĩĐŊ</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>â ī¸</emoji> <b>ĐŖĐēĐ°ĐļĐ¸ ĐŧĐžĐ´ŅĐģŅ Đ´ĐģŅ"
            " ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐĩĐ˛ĐĩŅĐŊĐ°Ņ ĐēĐžĐ´Đ¸ŅĐžĐ˛ĐēĐ°"
            " ĐŧĐžĐ´ŅĐģŅ</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐ°ĐŗŅŅĐˇĐēĐ° ĐŊĐĩ"
            " ŅĐ˛ĐĩĐŊŅĐ°ĐģĐ°ŅŅ ŅŅĐŋĐĩŅĐžĐŧ. ĐĄĐŧĐžŅŅĐ¸ ĐģĐžĐŗĐ¸.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>đ</emoji> <b>ĐĐžĐ´ŅĐģŅ"
            "</b> <code>{}</code>{} <b>ĐˇĐ°ĐŗŅŅĐļĐĩĐŊ {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Đ ŅŅĐž Đ˛ŅĐŗŅŅĐļĐ°ŅŅ ŅĐž?</b>",
        "unloaded": "{} <b>ĐĐžĐ´ŅĐģŅ {} Đ˛ŅĐŗŅŅĐļĐĩĐŊ.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐžĐ´ŅĐģŅ ĐŊĐĩ"
            " Đ˛ŅĐŗŅŅĐļĐĩĐŊ.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐŅĐ¸ĐąĐēĐ° ŅŅŅĐ°ĐŊĐžĐ˛ĐēĐ¸"
            " ĐˇĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐĩĐš</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>đļ</emoji> <b>ĐŅĐ¸ĐąĐēĐ° ŅŅŅĐ°ĐŊĐžĐ˛ĐēĐ¸"
            " ĐˇĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐĩĐš</b>\n<b>ĐĐ°Đ¸ĐąĐžĐģĐĩĐĩ ŅĐ°ŅŅĐž Đ˛ĐžĐˇĐŊĐ¸ĐēĐ°ĐĩŅ Đ¸Đˇ-ĐˇĐ° ŅĐžĐŗĐž, ŅŅĐž Termux ĐŊĐĩ"
            " ĐŋĐžĐ´Đ´ĐĩŅĐļĐ¸Đ˛Đ°ĐĩŅ ĐŧĐŊĐžĐŗĐ¸Đĩ ĐąĐ¸ĐąĐģĐ¸ĐžŅĐĩĐēĐ¸. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ ĐžĐą ŅŅĐžĐŧ ĐēĐ°Đē ĐžĐą ĐžŅĐ¸ĐąĐēĐĩ, ŅŅĐž"
            " ĐŊĐĩ ĐŧĐžĐļĐĩŅ ĐąŅŅŅ Đ¸ŅĐŋŅĐ°Đ˛ĐģĐĩĐŊĐž.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>đ</emoji> <b>ĐŖŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°Ņ"
            " ĐˇĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐ¸:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>đ</emoji> <b>ĐĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐ¸"
            " ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊŅ, ĐŊĐž ĐŊŅĐļĐŊĐ° ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐ° Đ´ĐģŅ ĐŋŅĐ¸ĐŧĐĩĐŊĐĩĐŊĐ¸Ņ</b> <code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>ĐĐžĐ´ŅĐģĐ¸ ŅĐ´Đ°ĐģĐĩĐŊŅ</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>đ¤ˇââī¸</emoji> ĐĐĩŅ ĐžĐŋĐ¸ŅĐ°ĐŊĐ¸Ņ",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>đ¤</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžĐŧŅ ĐŧĐžĐ´ŅĐģŅ"
            " ŅŅĐĩĐąŅĐĩŅŅŅ Hikka Đ˛ĐĩŅŅĐ¸Đ¸ {}+\nĐĐąĐŊĐžĐ˛Đ¸ŅŅ Ņ ĐŋĐžĐŧĐžŅŅŅ</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžĐŧŅ ĐŧĐžĐ´ŅĐģŅ"
            " ŅŅĐĩĐąŅĐĩŅŅŅ FFMPEG, ĐēĐžŅĐžŅŅĐš ĐŊĐĩ ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊ</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>đĢļ</emoji> <b>Đ Đ°ĐˇŅĐ°ĐąĐžŅŅĐ¸Đē:"
            "</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>đĻ</emoji> <b>ĐĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐ¸:"
            "</b> \n{}"
        ),
        "by": "ĐžŅ",
        "module_fs": (
            "đŋ <b>ĐĸŅ ŅĐžŅĐĩŅŅ ŅĐžŅŅĐ°ĐŊĐ¸ŅŅ ĐŧĐžĐ´ŅĐģŅ ĐŊĐ° ĐļĐĩŅŅĐēĐ¸Đš Đ´Đ¸ŅĐē, ŅŅĐžĐąŅ ĐžĐŊ ĐŊĐĩ Đ˛ŅĐŗŅŅĐļĐ°ĐģŅŅ"
            " ĐŋŅĐ¸ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐĩ?</b>"
        ),
        "save": "đŋ ĐĄĐžŅŅĐ°ĐŊĐ¸ŅŅ",
        "no_save": "đĢ ĐĐĩ ŅĐžŅŅĐ°ĐŊŅŅŅ",
        "save_for_all": "đŊ ĐŅĐĩĐŗĐ´Đ° ŅĐžŅŅĐ°ĐŊŅŅŅ",
        "never_save": "đĢ ĐĐ¸ĐēĐžĐŗĐ´Đ° ĐŊĐĩ ŅĐžŅŅĐ°ĐŊŅŅŅ",
        "will_save_fs": (
            "đŊ ĐĸĐĩĐŋĐĩŅŅ Đ˛ŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸, ĐˇĐ°ĐŗŅŅĐļĐĩĐŊĐŊŅĐĩ Đ¸Đˇ ŅĐ°ĐšĐģĐ°, ĐąŅĐ´ŅŅ ŅĐžŅŅĐ°ĐŊŅŅŅŅŅ ĐŊĐ° ĐļĐĩŅŅĐēĐ¸Đš"
            " Đ´Đ¸ŅĐē"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžĐŧŅ ĐŧĐžĐ´ŅĐģŅ ĐŊŅĐļĐĩĐŊ"
            " NetfollInline, Đ° Đ¸ĐŊĐ¸ŅĐ¸Đ°ĐģĐ¸ĐˇĐ°ŅĐ¸Ņ ĐŧĐĩĐŊĐĩĐ´ĐļĐĩŅĐ° Đ¸ĐŊĐģĐ°ĐšĐŊĐ° ĐŊĐĩŅĐ´Đ°ŅĐŊĐ°</b>\n<i>ĐĐžĐŋŅĐžĐąŅĐš"
            " ŅĐ´Đ°ĐģĐ¸ŅŅ ĐžĐ´ĐŊĐžĐŗĐž Đ¸Đˇ ŅŅĐ°ŅŅŅ ĐąĐžŅĐžĐ˛ Đ˛ @BotFather Đ¸ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐ¸ŅŅ ŅĐˇĐĩŅĐąĐžŅĐ°</i>"
        ),
        "_cmd_doc_dlmod": "ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ Đ¸ ŅŅŅĐ°ĐŊĐ°ĐģĐ˛Đ¸Đ˛Đ°ĐĩŅ ĐŧĐžĐ´ŅĐģŅ Đ¸Đˇ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Ņ",
        "_cmd_doc_dlpreset": "ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ Đ¸ ŅŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°ĐĩŅ ĐžĐŋŅĐĩĐ´ĐĩĐģĐĩĐŊĐŊŅĐš ĐŊĐ°ĐąĐžŅ ĐŧĐžĐ´ŅĐģĐĩĐš",
        "_cmd_doc_loadmod": "ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ Đ¸ ŅŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°ĐĩŅ ĐŧĐžĐ´ŅĐģŅ Đ¸Đˇ ŅĐ°ĐšĐģĐ°",
        "_cmd_doc_unloadmod": "ĐŅĐŗŅŅĐļĐ°ĐĩŅ (ŅĐ´Đ°ĐģŅĐĩŅ) ĐŧĐžĐ´ŅĐģŅ",
        "_cmd_doc_clearmodules": "ĐŅĐŗŅŅĐļĐ°ĐĩŅ Đ˛ŅĐĩ ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊĐŊŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸",
        "_cls_doc": "ĐĐ°ĐŗŅŅĐļĐ°ĐĩŅ ĐŧĐžĐ´ŅĐģĐ¸",
        "share_link_doc": "ĐŖĐēĐ°ĐˇŅĐ˛Đ°ŅŅ ŅŅŅĐģĐēŅ ĐŊĐ° ĐŧĐžĐ´ŅĐģŅ ĐŋĐžŅĐģĐĩ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ŅĐĩŅĐĩĐˇ .dlmod",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>đ</emoji> <b>ĐĄŅŅĐģĐēĐ°:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>â ī¸</emoji> <b>ĐĐĩ Đ¸ŅĐŋĐžĐģŅĐˇŅĐš"
            " `blob` ŅŅŅĐģĐēĐ¸ Đ´ĐģŅ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ĐŧĐžĐ´ŅĐģĐĩĐš. ĐŅŅŅĐĩ ĐˇĐ°ĐŗŅŅĐļĐ°ŅŅ Đ¸Đˇ `raw`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>đ</emoji> <b>ĐĄŅŅĐģĐēĐ°:"
            "</b> <code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\nâ­ī¸ <b>Đ­ŅĐžŅ ĐŧĐžĐ´ŅĐģŅ"
            " ŅĐ´ĐĩĐģĐ°ĐŊ {}. ĐĐžĐ´ĐŋĐ¸ŅĐ°ŅŅŅŅ ĐŊĐ° ĐŊĐĩĐŗĐž, ŅŅĐžĐąŅ ĐŋĐžĐ´Đ´ĐĩŅĐļĐ°ŅŅ ŅĐ°ĐˇŅĐ°ĐąĐžŅŅĐ¸ĐēĐ°?</b>"
        ),
        "subscribe": "đŦ ĐĐžĐ´ĐŋĐ¸ŅĐ°ŅŅŅŅ",
        "no_subscribe": "đĢ ĐĐĩ ĐŋĐžĐ´ĐŋĐ¸ŅŅĐ˛Đ°ŅŅŅŅ",
        "subscribed": "đŦ ĐĐžĐ´ĐŋĐ¸ŅĐ°ĐģŅŅ!",
        "unsubscribed": "đĢ Đ¯ ĐąĐžĐģŅŅĐĩ ĐŊĐĩ ĐąŅĐ´Ņ ĐŋŅĐĩĐ´ĐģĐ°ĐŗĐ°ŅŅ ĐŋĐžĐ´ĐŋĐ¸ŅĐ°ŅŅŅŅ ĐŊĐ° ŅŅĐžŅ ĐēĐ°ĐŊĐ°Đģ",
        "confirm_clearmodules": (
            "â ī¸ <b>ĐŅ ŅĐ˛ĐĩŅĐĩĐŊŅ, ŅŅĐž ŅĐžŅĐ¸ŅĐĩ Đ˛ŅĐŗŅŅĐˇĐ¸ŅŅ Đ˛ŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸?</b>"
        ),
        "clearmodules": "đ ĐŅĐŗŅŅĐˇĐ¸ŅŅ ĐŧĐžĐ´ŅĐģĐ¸",
        "cancel": "đĢ ĐŅĐŧĐĩĐŊĐ°",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžŅ ĐŧĐžĐ´ŅĐģŅ"
            " ĐŋĐžĐŋŅŅĐ°ĐģŅŅ ĐŋĐĩŅĐĩĐˇĐ°ĐŋĐ¸ŅĐ°ŅŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅĐš (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Đ­ŅĐž ĐŊĐĩ ĐžŅĐ¸ĐąĐēĐ°, Đ° ĐŧĐĩŅĐ°"
            " ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžŅŅĐ¸, ŅŅĐĩĐąŅĐĩĐŧĐ°Ņ Đ´ĐģŅ ĐŋŅĐĩĐ´ĐžŅĐ˛ŅĐ°ŅĐĩĐŊĐ¸Ņ ĐˇĐ°ĐŧĐĩĐŊŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ ĐŧĐžĐ´ŅĐģĐĩĐš"
            " Đ˛ŅŅĐēĐ¸Đŧ ŅĐģĐ°ĐŧĐžĐŧ. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ Đž ĐŊĐĩĐš Đ˛ support ŅĐ°ŅĐĩ</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžŅ ĐŧĐžĐ´ŅĐģŅ"
            " ĐŋĐžĐŋŅŅĐ°ĐģŅŅ ĐŋĐĩŅĐĩĐˇĐ°ĐŋĐ¸ŅĐ°ŅŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ ĐēĐžĐŧĐ°ĐŊĐ´Ņ"
            " (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Đ­ŅĐž ĐŊĐĩ ĐžŅĐ¸ĐąĐēĐ°, Đ° ĐŧĐĩŅĐ°"
            " ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžŅŅĐ¸, ŅŅĐĩĐąŅĐĩĐŧĐ°Ņ Đ´ĐģŅ ĐŋŅĐĩĐ´ĐžŅĐ˛ŅĐ°ŅĐĩĐŊĐ¸Ņ ĐˇĐ°ĐŧĐĩĐŊŅ ĐēĐžĐŧĐ°ĐŊĐ´ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ"
            " ĐŧĐžĐ´ŅĐģĐĩĐš Đ˛ŅŅĐēĐ¸Đŧ ŅĐģĐ°ĐŧĐžĐŧ. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ Đž ĐŊĐĩĐš Đ˛ support ŅĐ°ŅĐĩ</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>ĐĸŅ ĐŊĐĩ ĐŧĐžĐļĐĩŅŅ"
            " Đ˛ŅĐŗŅŅĐˇĐ¸ŅŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅĐš ĐŧĐžĐ´ŅĐģŅ</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Đ­ŅĐž ĐŊĐĩ ĐžŅĐ¸ĐąĐēĐ°, Đ° ĐŧĐĩŅĐ°"
            " ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžŅŅĐ¸, ŅŅĐĩĐąŅĐĩĐŧĐ°Ņ Đ´ĐģŅ ĐŋŅĐĩĐ´ĐžŅĐ˛ŅĐ°ŅĐĩĐŊĐ¸Ņ ĐˇĐ°ĐŧĐĩĐŊŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ ĐŧĐžĐ´ŅĐģĐĩĐš"
            " Đ˛ŅŅĐēĐ¸Đŧ ŅĐģĐ°ĐŧĐžĐŧ. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ Đž ĐŊĐĩĐš Đ˛ support ŅĐ°ŅĐĩ</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>ĐĸŅ ĐŊĐĩ ĐŧĐžĐļĐĩŅŅ"
            " Đ˛ŅĐŗŅŅĐˇĐ¸ŅŅ ĐąĐ¸ĐąĐģĐ¸ĐžŅĐĩĐēŅ</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>đĢ</emoji> <b>ĐĐžĐ´ŅĐģŅ"
            "</b> <code>{}</code> <b>ĐˇĐ°ĐŋŅĐ°ŅĐ¸Đ˛Đ°ĐĩŅ ŅĐ°ĐˇŅĐĩŅĐĩĐŊĐ¸Đĩ ĐŊĐ° Đ˛ŅŅŅĐŋĐģĐĩĐŊĐ¸Đĩ Đ˛ ĐēĐ°ĐŊĐ°Đģ <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">â</emoji> ĐŅĐ¸ŅĐ¸ĐŊĐ°:'
            ' {}</b>\n\n<i>ĐĐļĐ¸Đ´Đ°ĐŊĐ¸Đĩ <a href="https://t.me/{}">ĐŋĐžĐ´ŅĐ˛ĐĩŅĐļĐ´ĐĩĐŊĐ¸Ņ</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>đ</emoji> <b>ĐŖŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°Ņ ĐŧĐžĐ´ŅĐģŅ"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>ŅĐļĐĩ Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊ</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊ</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐŅ Đ´ĐžĐģĐļĐŊŅ ŅĐēĐ°ĐˇĐ°ŅŅ"
            " ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš Đ´ĐģŅ Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊĐ¸Ņ</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>ĐŊĐĩ Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊ</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>ŅĐ´Đ°ĐģĐĩĐŊ</b>"
        ),
    }
    # ĐĐĐ ĐĐĐĐĄĐĸĐ!!!
    strings_uk = {
        "repo_config_doc": "ĐĄŅŅĐģĐēĐ° Đ´ĐģŅ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ĐŧĐžĐ´ŅĐģĐĩĐš",
        "add_repo_config_doc": "ĐĐžĐŋĐžĐģĐŊĐ¸ŅĐĩĐģŅĐŊŅĐĩ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đ¸",
        "avail_header": "đĸ <b>ĐŅĐ¸ŅĐ¸Đ°ĐģŅĐŊŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸ Đ¸Đˇ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Ņ</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>â ī¸</emoji> <b>ĐŅĐąĐĩŅĐ¸ ĐŋŅĐĩŅĐĩŅ</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐŅĐĩŅĐĩŅ ĐŊĐĩ ĐŊĐ°ĐšĐ´ĐĩĐŊ</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>ĐŅĐĩŅĐĩŅ ĐˇĐ°ĐŗŅŅĐļĐĩĐŊ</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐžĐ´ŅĐģŅ ĐŊĐĩĐ´ĐžŅŅŅĐŋĐĩĐŊ Đ˛"
            " ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đ¸.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Đ¤Đ°ĐšĐģ ĐŊĐĩ ĐŊĐ°ĐšĐ´ĐĩĐŊ</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>â ī¸</emoji> <b>ĐŖĐēĐ°ĐļĐ¸ ĐŧĐžĐ´ŅĐģŅ Đ´ĐģŅ"
            " ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐĩĐ˛ĐĩŅĐŊĐ°Ņ ĐēĐžĐ´Đ¸ŅĐžĐ˛ĐēĐ°"
            " ĐŧĐžĐ´ŅĐģŅ</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐ°ĐŗŅŅĐˇĐēĐ° ĐŊĐĩ"
            " ŅĐ˛ĐĩĐŊŅĐ°ĐģĐ°ŅŅ ŅŅĐŋĐĩŅĐžĐŧ. ĐĄĐŧĐžŅŅĐ¸ ĐģĐžĐŗĐ¸.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>đ</emoji> <b>ĐĐžĐ´ŅĐģŅ"
            "</b> <code>{}</code>{} <b>ĐˇĐ°ĐŗŅŅĐļĐĩĐŊ {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Đ ŅŅĐž Đ˛ŅĐŗŅŅĐļĐ°ŅŅ ŅĐž?</b>",
        "unloaded": "{} <b>ĐĐžĐ´ŅĐģŅ {} Đ˛ŅĐŗŅŅĐļĐĩĐŊ.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐĐžĐ´ŅĐģŅ ĐŊĐĩ"
            " Đ˛ŅĐŗŅŅĐļĐĩĐŊ.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐŅĐ¸ĐąĐēĐ° ŅŅŅĐ°ĐŊĐžĐ˛ĐēĐ¸"
            " ĐˇĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐĩĐš</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>đļ</emoji> <b>ĐŅĐ¸ĐąĐēĐ° ŅŅŅĐ°ĐŊĐžĐ˛ĐēĐ¸"
            " ĐˇĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐĩĐš</b>\n<b>ĐĐ°Đ¸ĐąĐžĐģĐĩĐĩ ŅĐ°ŅŅĐž Đ˛ĐžĐˇĐŊĐ¸ĐēĐ°ĐĩŅ Đ¸Đˇ-ĐˇĐ° ŅĐžĐŗĐž, ŅŅĐž Termux ĐŊĐĩ"
            " ĐŋĐžĐ´Đ´ĐĩŅĐļĐ¸Đ˛Đ°ĐĩŅ ĐŧĐŊĐžĐŗĐ¸Đĩ ĐąĐ¸ĐąĐģĐ¸ĐžŅĐĩĐēĐ¸. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ ĐžĐą ŅŅĐžĐŧ ĐēĐ°Đē ĐžĐą ĐžŅĐ¸ĐąĐēĐĩ, ŅŅĐž"
            " ĐŊĐĩ ĐŧĐžĐļĐĩŅ ĐąŅŅŅ Đ¸ŅĐŋŅĐ°Đ˛ĐģĐĩĐŊĐž.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>đ</emoji> <b>ĐŖŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°Ņ"
            " ĐˇĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐ¸:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>đ</emoji> <b>ĐĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐ¸"
            " ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊŅ, ĐŊĐž ĐŊŅĐļĐŊĐ° ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐ° Đ´ĐģŅ ĐŋŅĐ¸ĐŧĐĩĐŊĐĩĐŊĐ¸Ņ</b> <code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>ĐĐžĐ´ŅĐģĐ¸ ŅĐ´Đ°ĐģĐĩĐŊŅ</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>đ¤ˇââī¸</emoji> ĐĐĩŅ ĐžĐŋĐ¸ŅĐ°ĐŊĐ¸Ņ",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>đ¤</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžĐŧŅ ĐŧĐžĐ´ŅĐģŅ"
            " ŅŅĐĩĐąŅĐĩŅŅŅ Hikka Đ˛ĐĩŅŅĐ¸Đ¸ {}+\nĐĐąĐŊĐžĐ˛Đ¸ŅŅ Ņ ĐŋĐžĐŧĐžŅŅŅ</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžĐŧŅ ĐŧĐžĐ´ŅĐģŅ"
            " ŅŅĐĩĐąŅĐĩŅŅŅ FFMPEG, ĐēĐžŅĐžŅŅĐš ĐŊĐĩ ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊ</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>đĢļ</emoji> <b>Đ Đ°ĐˇŅĐ°ĐąĐžŅŅĐ¸Đē:"
            "</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>đĻ</emoji> <b>ĐĐ°Đ˛Đ¸ŅĐ¸ĐŧĐžŅŅĐ¸:"
            "</b> \n{}"
        ),
        "by": "ĐžŅ",
        "module_fs": (
            "đŋ <b>ĐĸŅ ŅĐžŅĐĩŅŅ ŅĐžŅŅĐ°ĐŊĐ¸ŅŅ ĐŧĐžĐ´ŅĐģŅ ĐŊĐ° ĐļĐĩŅŅĐēĐ¸Đš Đ´Đ¸ŅĐē, ŅŅĐžĐąŅ ĐžĐŊ ĐŊĐĩ Đ˛ŅĐŗŅŅĐļĐ°ĐģŅŅ"
            " ĐŋŅĐ¸ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐĩ?</b>"
        ),
        "save": "đŋ ĐĄĐžŅŅĐ°ĐŊĐ¸ŅŅ",
        "no_save": "đĢ ĐĐĩ ŅĐžŅŅĐ°ĐŊŅŅŅ",
        "save_for_all": "đŊ ĐŅĐĩĐŗĐ´Đ° ŅĐžŅŅĐ°ĐŊŅŅŅ",
        "never_save": "đĢ ĐĐ¸ĐēĐžĐŗĐ´Đ° ĐŊĐĩ ŅĐžŅŅĐ°ĐŊŅŅŅ",
        "will_save_fs": (
            "đŊ ĐĸĐĩĐŋĐĩŅŅ Đ˛ŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸, ĐˇĐ°ĐŗŅŅĐļĐĩĐŊĐŊŅĐĩ Đ¸Đˇ ŅĐ°ĐšĐģĐ°, ĐąŅĐ´ŅŅ ŅĐžŅŅĐ°ĐŊŅŅŅŅŅ ĐŊĐ° ĐļĐĩŅŅĐēĐ¸Đš"
            " Đ´Đ¸ŅĐē"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžĐŧŅ ĐŧĐžĐ´ŅĐģŅ ĐŊŅĐļĐĩĐŊ"
            " NetfollInline, Đ° Đ¸ĐŊĐ¸ŅĐ¸Đ°ĐģĐ¸ĐˇĐ°ŅĐ¸Ņ ĐŧĐĩĐŊĐĩĐ´ĐļĐĩŅĐ° Đ¸ĐŊĐģĐ°ĐšĐŊĐ° ĐŊĐĩŅĐ´Đ°ŅĐŊĐ°</b>\n<i>ĐĐžĐŋŅĐžĐąŅĐš"
            " ŅĐ´Đ°ĐģĐ¸ŅŅ ĐžĐ´ĐŊĐžĐŗĐž Đ¸Đˇ ŅŅĐ°ŅŅŅ ĐąĐžŅĐžĐ˛ Đ˛ @BotFather Đ¸ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐ¸ŅŅ ŅĐˇĐĩŅĐąĐžŅĐ°</i>"
        ),
        "_cmd_doc_dlmod": "ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ Đ¸ ŅŅŅĐ°ĐŊĐ°ĐģĐ˛Đ¸Đ˛Đ°ĐĩŅ ĐŧĐžĐ´ŅĐģŅ Đ¸Đˇ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Ņ",
        "_cmd_doc_dlpreset": "ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ Đ¸ ŅŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°ĐĩŅ ĐžĐŋŅĐĩĐ´ĐĩĐģĐĩĐŊĐŊŅĐš ĐŊĐ°ĐąĐžŅ ĐŧĐžĐ´ŅĐģĐĩĐš",
        "_cmd_doc_loadmod": "ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ Đ¸ ŅŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°ĐĩŅ ĐŧĐžĐ´ŅĐģŅ Đ¸Đˇ ŅĐ°ĐšĐģĐ°",
        "_cmd_doc_unloadmod": "ĐŅĐŗŅŅĐļĐ°ĐĩŅ (ŅĐ´Đ°ĐģŅĐĩŅ) ĐŧĐžĐ´ŅĐģŅ",
        "_cmd_doc_clearmodules": "ĐŅĐŗŅŅĐļĐ°ĐĩŅ Đ˛ŅĐĩ ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊĐŊŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸",
        "_cls_doc": "ĐĐ°ĐŗŅŅĐļĐ°ĐĩŅ ĐŧĐžĐ´ŅĐģĐ¸",
        "share_link_doc": "ĐŖĐēĐ°ĐˇŅĐ˛Đ°ŅŅ ŅŅŅĐģĐēŅ ĐŊĐ° ĐŧĐžĐ´ŅĐģŅ ĐŋĐžŅĐģĐĩ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ŅĐĩŅĐĩĐˇ .dlmod",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>đ</emoji> <b>ĐĄŅŅĐģĐēĐ°:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>â ī¸</emoji> <b>ĐĐĩ Đ¸ŅĐŋĐžĐģŅĐˇŅĐš"
            " `blob` ŅŅŅĐģĐēĐ¸ Đ´ĐģŅ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ĐŧĐžĐ´ŅĐģĐĩĐš. ĐŅŅŅĐĩ ĐˇĐ°ĐŗŅŅĐļĐ°ŅŅ Đ¸Đˇ `raw`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>đ</emoji> <b>ĐĄŅŅĐģĐēĐ°:"
            "</b> <code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\nâ­ī¸ <b>Đ­ŅĐžŅ ĐŧĐžĐ´ŅĐģŅ"
            " ŅĐ´ĐĩĐģĐ°ĐŊ {}. ĐĐžĐ´ĐŋĐ¸ŅĐ°ŅŅŅŅ ĐŊĐ° ĐŊĐĩĐŗĐž, ŅŅĐžĐąŅ ĐŋĐžĐ´Đ´ĐĩŅĐļĐ°ŅŅ ŅĐ°ĐˇŅĐ°ĐąĐžŅŅĐ¸ĐēĐ°?</b>"
        ),
        "subscribe": "đŦ ĐĐžĐ´ĐŋĐ¸ŅĐ°ŅŅŅŅ",
        "no_subscribe": "đĢ ĐĐĩ ĐŋĐžĐ´ĐŋĐ¸ŅŅĐ˛Đ°ŅŅŅŅ",
        "subscribed": "đŦ ĐĐžĐ´ĐŋĐ¸ŅĐ°ĐģŅŅ!",
        "unsubscribed": "đĢ Đ¯ ĐąĐžĐģŅŅĐĩ ĐŊĐĩ ĐąŅĐ´Ņ ĐŋŅĐĩĐ´ĐģĐ°ĐŗĐ°ŅŅ ĐŋĐžĐ´ĐŋĐ¸ŅĐ°ŅŅŅŅ ĐŊĐ° ŅŅĐžŅ ĐēĐ°ĐŊĐ°Đģ",
        "confirm_clearmodules": (
            "â ī¸ <b>ĐŅ ŅĐ˛ĐĩŅĐĩĐŊŅ, ŅŅĐž ŅĐžŅĐ¸ŅĐĩ Đ˛ŅĐŗŅŅĐˇĐ¸ŅŅ Đ˛ŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸?</b>"
        ),
        "clearmodules": "đ ĐŅĐŗŅŅĐˇĐ¸ŅŅ ĐŧĐžĐ´ŅĐģĐ¸",
        "cancel": "đĢ ĐŅĐŧĐĩĐŊĐ°",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžŅ ĐŧĐžĐ´ŅĐģŅ"
            " ĐŋĐžĐŋŅŅĐ°ĐģŅŅ ĐŋĐĩŅĐĩĐˇĐ°ĐŋĐ¸ŅĐ°ŅŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅĐš (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Đ­ŅĐž ĐŊĐĩ ĐžŅĐ¸ĐąĐēĐ°, Đ° ĐŧĐĩŅĐ°"
            " ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžŅŅĐ¸, ŅŅĐĩĐąŅĐĩĐŧĐ°Ņ Đ´ĐģŅ ĐŋŅĐĩĐ´ĐžŅĐ˛ŅĐ°ŅĐĩĐŊĐ¸Ņ ĐˇĐ°ĐŧĐĩĐŊŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ ĐŧĐžĐ´ŅĐģĐĩĐš"
            " Đ˛ŅŅĐēĐ¸Đŧ ŅĐģĐ°ĐŧĐžĐŧ. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ Đž ĐŊĐĩĐš Đ˛ support ŅĐ°ŅĐĩ</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>Đ­ŅĐžŅ ĐŧĐžĐ´ŅĐģŅ"
            " ĐŋĐžĐŋŅŅĐ°ĐģŅŅ ĐŋĐĩŅĐĩĐˇĐ°ĐŋĐ¸ŅĐ°ŅŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ ĐēĐžĐŧĐ°ĐŊĐ´Ņ"
            " (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Đ­ŅĐž ĐŊĐĩ ĐžŅĐ¸ĐąĐēĐ°, Đ° ĐŧĐĩŅĐ°"
            " ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžŅŅĐ¸, ŅŅĐĩĐąŅĐĩĐŧĐ°Ņ Đ´ĐģŅ ĐŋŅĐĩĐ´ĐžŅĐ˛ŅĐ°ŅĐĩĐŊĐ¸Ņ ĐˇĐ°ĐŧĐĩĐŊŅ ĐēĐžĐŧĐ°ĐŊĐ´ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ"
            " ĐŧĐžĐ´ŅĐģĐĩĐš Đ˛ŅŅĐēĐ¸Đŧ ŅĐģĐ°ĐŧĐžĐŧ. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ Đž ĐŊĐĩĐš Đ˛ support ŅĐ°ŅĐĩ</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>ĐĸŅ ĐŊĐĩ ĐŧĐžĐļĐĩŅŅ"
            " Đ˛ŅĐŗŅŅĐˇĐ¸ŅŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅĐš ĐŧĐžĐ´ŅĐģŅ</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>đĄ</emoji><i> Đ­ŅĐž ĐŊĐĩ ĐžŅĐ¸ĐąĐēĐ°, Đ° ĐŧĐĩŅĐ°"
            " ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžŅŅĐ¸, ŅŅĐĩĐąŅĐĩĐŧĐ°Ņ Đ´ĐģŅ ĐŋŅĐĩĐ´ĐžŅĐ˛ŅĐ°ŅĐĩĐŊĐ¸Ņ ĐˇĐ°ĐŧĐĩĐŊŅ Đ˛ŅŅŅĐžĐĩĐŊĐŊŅŅ ĐŧĐžĐ´ŅĐģĐĩĐš"
            " Đ˛ŅŅĐēĐ¸Đŧ ŅĐģĐ°ĐŧĐžĐŧ. ĐĐĩ ŅĐžĐžĐąŅĐ°ĐšŅĐĩ Đž ĐŊĐĩĐš Đ˛ support ŅĐ°ŅĐĩ</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>đ</emoji> <b>ĐĸŅ ĐŊĐĩ ĐŧĐžĐļĐĩŅŅ"
            " Đ˛ŅĐŗŅŅĐˇĐ¸ŅŅ ĐąĐ¸ĐąĐģĐ¸ĐžŅĐĩĐēŅ</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>đĢ</emoji> <b>ĐĐžĐ´ŅĐģŅ"
            "</b> <code>{}</code> <b>ĐˇĐ°ĐŋŅĐ°ŅĐ¸Đ˛Đ°ĐĩŅ ŅĐ°ĐˇŅĐĩŅĐĩĐŊĐ¸Đĩ ĐŊĐ° Đ˛ŅŅŅĐŋĐģĐĩĐŊĐ¸Đĩ Đ˛ ĐēĐ°ĐŊĐ°Đģ <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">â</emoji> ĐŅĐ¸ŅĐ¸ĐŊĐ°:'
            ' {}</b>\n\n<i>ĐĐļĐ¸Đ´Đ°ĐŊĐ¸Đĩ <a href="https://t.me/{}">ĐŋĐžĐ´ŅĐ˛ĐĩŅĐļĐ´ĐĩĐŊĐ¸Ņ</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>đ</emoji> <b>ĐŖŅŅĐ°ĐŊĐ°Đ˛ĐģĐ¸Đ˛Đ°Ņ ĐŧĐžĐ´ŅĐģŅ"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>ŅĐļĐĩ Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊ</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊ</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>ĐŅ Đ´ĐžĐģĐļĐŊŅ ŅĐēĐ°ĐˇĐ°ŅŅ"
            " ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš Đ´ĐģŅ Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊĐ¸Ņ</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>đĢ</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>ĐŊĐĩ Đ´ĐžĐąĐ°Đ˛ĐģĐĩĐŊ</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>â</emoji> <b>Đ ĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš</b>"
            " <code>{}</code> <b>ŅĐ´Đ°ĐģĐĩĐŊ</b>"
        ),
    }

    fully_loaded = False
    _links_cache = {}

    def __init__(self):

        self._storage = RemoteStorage()

        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "MODULES_REPO",
                "https://mods.hikariatama.ru",
                lambda: self.strings("repo_config_doc"),
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "ADDITIONAL_REPOS",
                # Currenly the trusted developers are specified
                [
                    "https://github.com/MXRRI/Modules/raw/master"
                    "https://github.com/Den4ikSuperOstryyPer4ik/Astro-Modules/raw/main"
                    "https://github.com/hikariatama/host/raw/master",
                    "https://github.com/MoriSummerz/ftg-mods/raw/main",
                    "https://gitlab.com/CakesTwix/friendly-userbot-modules/-/raw/master",
                ],
                lambda: self.strings("add_repo_config_doc"),
                validator=loader.validators.Series(validator=loader.validators.Link()),
            ),
            loader.ConfigValue(
                "share_link",
                doc=lambda: self.strings("share_link_doc"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def _async_init(self):
        modules = list(
            filter(
                lambda x: not x.startswith("https://mods.hikariatama.ru"),
                utils.array_sum(
                    map(
                        lambda x: list(x.values()),
                        (await self.get_repo_list("full")).values(),
                    )
                ),
            )
        )
        logger.debug("Modules: %s", modules)
        asyncio.ensure_future(self._storage.preload(modules))
        asyncio.ensure_future(self._storage.preload_main_repo())

    async def client_ready(self):
        self._token_msg = (await self._client.get_messages("@hikka_ub", ids=[10]))[0]

        self.allmodules.add_aliases(self.lookup("settings").get("aliases", {}))

        main.hikka.ready.set()

        asyncio.ensure_future(self._update_modules())
        asyncio.ensure_future(self._async_init())

    @loader.loop(interval=3, wait_before=True, autostart=True)
    async def _config_autosaver(self):
        for mod in self.allmodules.modules:
            if (
                not hasattr(mod, "config")
                or not mod.config
                or not isinstance(mod.config, loader.ModuleConfig)
            ):
                continue

            for option, config in mod.config._config.items():
                if not hasattr(config, "_save_marker"):
                    continue

                delattr(mod.config._config[option], "_save_marker")
                mod.pointer("__config__", {})[option] = config.value

        for lib in self.allmodules.libraries:
            if (
                not hasattr(lib, "config")
                or not lib.config
                or not isinstance(lib.config, loader.ModuleConfig)
            ):
                continue

            for option, config in lib.config._config.items():
                if not hasattr(config, "_save_marker"):
                    continue

                delattr(lib.config._config[option], "_save_marker")
                lib._lib_pointer("__config__", {})[option] = config.value

        self._db.save()

    def update_modules_in_db(self):
        if self.allmodules.secure_boot:
            return

        self.set(
            "loaded_modules",
            {
                **{
                    module.__class__.__name__: module.__origin__
                    for module in self.allmodules.modules
                    if module.__origin__.startswith("http")
                },
                **{
                    module.name: module.url
                    for module in self.allmodules.dragon_modules
                    if module.url
                },
            },
        )

    @loader.owner
    @loader.command(
        ru_doc="ĐĐ°ĐŗŅŅĐˇĐ¸ŅŅ ĐŧĐžĐ´ŅĐģŅ Đ¸Đˇ ĐžŅĐ¸ŅĐ¸Đ°ĐģŅĐŊĐžĐŗĐž ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Ņ",
        it_doc="Carica un modulo dal repository ufficiale",
        de_doc="Lade ein Modul aus dem offiziellen Repository",
        tr_doc="Resmi depodan bir modÃŧl yÃŧkler",
        uz_doc="Ofitsial repodan modulni yuklash",
        es_doc="Cargar un mÃŗdulo desde el repositorio oficial",
        kk_doc="ĐŅĐ¸ŅĐ¸Đ°ĐģĐ´ŅŌ ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸ŅĐŊĐ°ĐŊ ĐŧĐžĐ´ŅĐģŅĐ´Ņ ĐļŌ¯ĐēŅĐĩŅ",
        alias="dlm",
    )
    async def dlmod(self, message: Message):
        """Install a module from the official module repo"""
        if args := utils.get_args(message):
            args = args[0]

            await self.download_and_install(args, message)
            if self.fully_loaded:
                self.update_modules_in_db()
        else:
            await self.inline.list(
                message,
                [
                    self.strings("avail_header")
                    + f"\nâī¸ {repo.strip('/')}\n\n"
                    + "\n".join(
                        [
                            " | ".join(chunk)
                            for chunk in utils.chunks(
                                [
                                    f"<code>{i}</code>"
                                    for i in sorted(
                                        [
                                            utils.escape_html(
                                                i.split("/")[-1].split(".")[0]
                                            )
                                            for i in mods.values()
                                        ]
                                    )
                                ],
                                5,
                            )
                        ]
                    )
                    for repo, mods in (await self.get_repo_list("full")).items()
                ],
            )

    @loader.owner
    @loader.command(
        ru_doc="ĐŖŅŅĐ°ĐŊĐžĐ˛Đ¸ŅŅ ĐŋŅĐĩŅĐĩŅ ĐŧĐžĐ´ŅĐģĐĩĐš",
        it_doc="Installa un preset di moduli",
        de_doc="Installiere ein Modul-Preset",
        tr_doc="ModÃŧl ÃļnbelleÄini yÃŧkle",
        uz_doc="Modul presetini o'rnatish",
        es_doc="Instalar un conjunto de mÃŗdulos",
        kk_doc="ĐĐžĐ´ŅĐģŅĐ´ŅŌŖ ĐŋŅĐĩŅĐĩŅŅĐŊ ĐžŅĐŊĐ°ŅŅ",
    )
    async def dlpreset(self, message: Message):
        """Set modules preset"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("select_preset"))
            return

        await self.get_repo_list(args[0])
        self.set("chosen_preset", args[0])

        await utils.answer(message, self.strings("preset_loaded"))
        await self.invoke("restart", "-f", message=message)

    async def _get_modules_to_load(self):
        preset = self.get("chosen_preset")

        if preset != "disable":
            possible_mods = (
                await self.get_repo_list(preset, only_primary=True)
            ).values()
            todo = dict(ChainMap(*possible_mods))
        else:
            todo = {}

        todo.update(**self.get("loaded_modules", {}))
        logger.debug("Loading modules: %s", todo)
        return todo

    async def _get_repo(self, repo: str, preset: str) -> str:
        repo = repo.strip("/")
        preset_id = f"{repo}/{preset}"

        if self._links_cache.get(preset_id, {}).get("exp", 0) >= time.time():
            return self._links_cache[preset_id]["data"]

        res = await utils.run_sync(
            requests.get,
            f"{repo}/{preset}.txt",
        )

        if not str(res.status_code).startswith("2"):
            logger.debug(
                "Can't load repo %s, preset %s because of %s status code",
                repo,
                preset,
                res.status_code,
            )
            return []

        self._links_cache[preset_id] = {
            "exp": time.time() + 5 * 60,
            "data": [link for link in res.text.strip().splitlines() if link],
        }

        return self._links_cache[preset_id]["data"]

    async def get_repo_list(
        self,
        preset: typing.Optional[str] = None,
        only_primary: bool = False,
    ) -> dict:
        if preset is None or preset == "none":
            preset = "minimal"

        return {
            repo: {
                f"Mod/{repo_id}/{i}": f'{repo.strip("/")}/{link}.py'
                for i, link in enumerate(set(await self._get_repo(repo, preset)))
            }
            for repo_id, repo in enumerate(
                [self.config["MODULES_REPO"]]
                + ([] if only_primary else self.config["ADDITIONAL_REPOS"])
            )
            if repo.startswith("http")
        }

    async def get_links_list(self) -> typing.List[str]:
        links = await self.get_repo_list("full")
        main_repo = list(links.pop(self.config["MODULES_REPO"]).values())
        return main_repo + list(dict(ChainMap(*list(links.values()))).values())

    async def _find_link(self, module_name: str) -> typing.Union[str, bool]:
        return next(
            filter(
                lambda link: link.lower().endswith(f"/{module_name.lower()}.py"),
                await self.get_links_list(),
            ),
            False,
        )

    async def download_and_install(
        self,
        module_name: str,
        message: typing.Optional[Message] = None,
    ):
        try:
            blob_link = False
            module_name = module_name.strip()
            if urlparse(module_name).netloc:
                url = module_name
                if re.match(
                    r"^(https:\/\/github\.com\/.*?\/.*?\/blob\/.*\.py)|"
                    r"(https:\/\/gitlab\.com\/.*?\/.*?\/-\/blob\/.*\.py)$",
                    url,
                ):
                    url = url.replace("/blob/", "/raw/")
                    blob_link = True
            else:
                url = await self._find_link(module_name)

                if not url:
                    if message is not None:
                        await utils.answer(message, self.strings("no_module"))

                    return False

            if message:
                message = await utils.answer(
                    message,
                    self.strings("installing").format(module_name),
                )

            try:
                r = await self._storage.fetch(url)
            except requests.exceptions.HTTPError:
                if message is not None:
                    await utils.answer(message, self.strings("no_module"))

                return False

            return await self.load_module(
                r,
                message,
                module_name,
                url,
                blob_link=blob_link,
            )
        except Exception:
            logger.exception("Failed to load %s", module_name)

    async def _inline__load(
        self,
        call: InlineCall,
        doc: str,
        path_: str,
        mode: str,
    ):
        save = False
        if mode == "all_yes":
            self._db.set(main.__name__, "permanent_modules_fs", True)
            self._db.set(main.__name__, "disable_modules_fs", False)
            await call.answer(self.strings("will_save_fs"))
            save = True
        elif mode == "all_no":
            self._db.set(main.__name__, "disable_modules_fs", True)
            self._db.set(main.__name__, "permanent_modules_fs", False)
        elif mode == "once":
            save = True

        await self.load_module(doc, call, origin=path_ or "<string>", save_fs=save)

    @loader.owner
    @loader.command(
        ru_doc="ĐĐ°ĐŗŅŅĐˇĐ¸ŅŅ ĐŧĐžĐ´ŅĐģŅ Đ¸Đˇ ŅĐ°ĐšĐģĐ°",
        it_doc="Carica un modulo da un file",
        de_doc="Lade Modul aus Datei",
        tr_doc="Dosyadan modÃŧl yÃŧkle",
        uz_doc="Fayldan modulni yuklash",
        es_doc="Cargar mÃŗdulo desde archivo",
        kk_doc="Đ¤Đ°ĐšĐģĐ´Đ°ĐŊ ĐŧĐžĐ´ŅĐģŅĐ´Ņ ĐļŌ¯ĐēŅĐĩŅ",
        alias="lm",
    )
    async def loadmod(self, message: Message):
        """Loads the module file"""
        msg = message if message.file else (await message.get_reply_message())

        if msg is None or msg.media is None:
            await utils.answer(message, self.strings("provide_module"))
            return

        path_ = None
        doc = await msg.download_media(bytes)

        logger.debug("Loading external module...")

        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await utils.answer(message, self.strings("bad_unicode"))
            return

        if not self._db.get(
            main.__name__,
            "disable_modules_fs",
            False,
        ) and not self._db.get(main.__name__, "permanent_modules_fs", False):
            if message.file:
                await message.edit("")
                message = await message.respond("đ", reply_to=utils.get_topic(message))

            if await self.inline.form(
                self.strings("module_fs"),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": self.strings("save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "once"),
                        },
                        {
                            "text": self.strings("no_save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "no"),
                        },
                    ],
                    [
                        {
                            "text": self.strings("save_for_all"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "all_yes"),
                        }
                    ],
                    [
                        {
                            "text": self.strings("never_save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "all_no"),
                        }
                    ],
                ],
            ):
                return

        if path_ is not None:
            await self.load_module(
                doc,
                message,
                origin=path_,
                save_fs=self._db.get(main.__name__, "permanent_modules_fs", False)
                and not self._db.get(main.__name__, "disable_modules_fs", False),
            )
        else:
            await self.load_module(
                doc,
                message,
                save_fs=self._db.get(main.__name__, "permanent_modules_fs", False)
                and not self._db.get(main.__name__, "disable_modules_fs", False),
            )

    async def load_module(
        self,
        doc: str,
        message: Message,
        name: typing.Optional[str] = None,
        origin: str = "<string>",
        did_requirements: bool = False,
        save_fs: bool = False,
        blob_link: bool = False,
    ):
        if any(
            line.replace(" ", "") == "#scope:ffmpeg" for line in doc.splitlines()
        ) and os.system("ffmpeg -version 1>/dev/null 2>/dev/null"):
            if isinstance(message, Message):
                await utils.answer(message, self.strings("ffmpeg_required"))
            return

        if (
            any(line.replace(" ", "") == "#scope:inline" for line in doc.splitlines())
            and not self.inline.init_complete
        ):
            if isinstance(message, Message):
                await utils.answer(message, self.strings("inline_init_failed"))
            return

        if re.search(r"# ?scope: ?hikka_min", doc):
            ver = re.search(r"# ?scope: ?hikka_min ((?:\d+\.){2}\d+)", doc).group(1)
            ver_ = tuple(map(int, ver.split(".")))
            if main.__version__ < ver_:
                if isinstance(message, Message):
                    if getattr(message, "file", None):
                        m = utils.get_chat_id(message)
                        await message.edit("")
                    else:
                        m = message

                    await self.inline.form(
                        self.strings("version_incompatible").format(ver),
                        m,
                        reply_markup=[
                            {
                                "text": self.lookup("updater").strings("btn_update"),
                                "callback": self.lookup("updater").inline_update,
                            },
                            {
                                "text": self.lookup("updater").strings("cancel"),
                                "action": "close",
                            },
                        ],
                    )
                return

        developer = re.search(r"# ?meta developer: ?(.+)", doc)
        developer = developer.group(1) if developer else False

        blob_link = self.strings("blob_link") if blob_link else ""

        if utils.check_url(name):
            url = copy.deepcopy(name)
        elif utils.check_url(origin):
            url = copy.deepcopy(origin)
        else:
            url = None

        if name is None:
            try:
                node = ast.parse(doc)
                uid = next(n.name for n in node.body if isinstance(n, ast.ClassDef))
            except Exception:
                logger.debug(
                    "Can't parse classname from code, using legacy uid instead",
                    exc_info=True,
                )
                uid = "__extmod_" + str(uuid.uuid4())
        else:
            if name.startswith(self.config["MODULES_REPO"]):
                name = name.split("/")[-1].split(".py")[0]

            uid = name.replace("%", "%%").replace(".", "%d")

        is_dragon = "@Client.on_message" in doc

        if is_dragon:
            module_name = f"dragon.modules.{uid}"
            if not self._client.pyro_proxy:
                self._client.pyro_proxy = PyroProxyClient(self._client)
                await self._client.pyro_proxy.start()
                await self._client.pyro_proxy.dispatcher.start()
                dragon.apply_compat(self._client)
        else:
            module_name = f"hikka.modules.{uid}"
            doc = geek.compat(doc)

        async def core_overwrite(e: CoreOverwriteError):
            nonlocal message

            with contextlib.suppress(Exception):
                self.allmodules.modules.remove(instance)

            if not message:
                return

            await utils.answer(
                message,
                self.strings(f"overwrite_{e.type}").format(
                    *(e.target,)
                    if e.type == "module"
                    else (self.get_prefix(), e.target)
                ),
            )

        async with (dragon.import_lock if is_dragon else lambda _: FakeLock())(
            self._client
        ):
            with (
                self._client.dragon_compat.misc.modules_help.get_notifier
                if is_dragon
                else FakeNotifier
            )() as notifier:
                try:
                    try:
                        spec = ModuleSpec(
                            module_name,
                            loader.StringLoader(doc, f"<external {module_name}>"),
                            origin=f"<external {module_name}>",
                        )
                        instance = await self.allmodules.register_module(
                            spec,
                            module_name,
                            origin,
                            save_fs=save_fs,
                            is_dragon=is_dragon,
                        )

                        if is_dragon:
                            dragon_module, instance = instance
                            instance.url = url
                    except ImportError as e:
                        logger.info(
                            "Module loading failed, attemping dependency installation"
                            " (%s)",
                            e.name,
                        )
                        # Let's try to reinstall dependencies
                        try:
                            requirements = list(
                                filter(
                                    lambda x: not x.startswith(("-", "_", ".")),
                                    map(
                                        str.strip,
                                        loader.VALID_PIP_PACKAGES.search(doc)[
                                            1
                                        ].split(),
                                    ),
                                )
                            )
                        except TypeError:
                            logger.warning(
                                "No valid pip packages specified in code, attemping"
                                " installation from error"
                            )
                            requirements = [
                                {
                                    "sklearn": "scikit-learn",
                                    "pil": "Pillow",
                                    "telethon": "Hikka-TL",
                                    "pyrogram": "Hikka-Pyro",
                                }.get(e.name.lower(), e.name)
                            ]

                        if not requirements:
                            raise Exception("Nothing to install") from e

                        logger.debug("Installing requirements: %s", requirements)

                        if did_requirements:
                            if message is not None:
                                await utils.answer(
                                    message,
                                    self.strings("requirements_restart").format(e.name),
                                )

                            return

                        if message is not None:
                            await utils.answer(
                                message,
                                self.strings("requirements_installing").format(
                                    "\n".join(
                                        "<emoji"
                                        " document_id=4971987363145188045>âĢī¸</emoji>"
                                        f" {req}"
                                        for req in requirements
                                    )
                                ),
                            )

                        pip = await asyncio.create_subprocess_exec(
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                            "-q",
                            "--disable-pip-version-check",
                            "--no-warn-script-location",
                            *["--user"] if loader.USER_INSTALL else [],
                            *requirements,
                        )

                        rc = await pip.wait()

                        if rc != 0:
                            if message is not None:
                                if "com.termux" in os.environ.get("PREFIX", ""):
                                    await utils.answer(
                                        message,
                                        self.strings("requirements_failed_termux"),
                                    )
                                else:
                                    await utils.answer(
                                        message,
                                        self.strings("requirements_failed"),
                                    )

                            return

                        importlib.invalidate_caches()

                        kwargs = utils.get_kwargs()
                        kwargs["did_requirements"] = True

                        return await self.load_module(**kwargs)  # Try again
                    except CoreOverwriteError as e:
                        await core_overwrite(e)
                        return
                    except loader.LoadError as e:
                        with contextlib.suppress(Exception):
                            await self.allmodules.unload_module(
                                instance.__class__.__name__
                            )

                        with contextlib.suppress(Exception):
                            self.allmodules.modules.remove(instance)

                        if message:
                            await utils.answer(
                                message,
                                "<emoji document_id=5454225457916420314>đ</emoji>"
                                f" <b>{utils.escape_html(str(e))}</b>",
                            )
                        return
                except Exception as e:
                    logger.exception("Loading external module failed due to %s", e)

                    if message is not None:
                        await utils.answer(message, self.strings("load_failed"))

                    return

                if hasattr(instance, "__version__") and isinstance(
                    instance.__version__, tuple
                ):
                    version = (
                        "<b><i>"
                        f" (v{'.'.join(list(map(str, list(instance.__version__))))})</i></b>"
                    )
                else:
                    version = ""

                try:
                    try:
                        self.allmodules.send_config_one(instance)

                        async def inner_proxy():
                            nonlocal instance, message
                            while True:
                                if hasattr(instance, "hikka_wait_channel_approve"):
                                    if message:
                                        (
                                            module,
                                            channel,
                                            reason,
                                        ) = instance.hikka_wait_channel_approve
                                        message = await utils.answer(
                                            message,
                                            self.strings("wait_channel_approve").format(
                                                module,
                                                channel.username,
                                                utils.escape_html(channel.title),
                                                utils.escape_html(reason),
                                                self.inline.bot_username,
                                            ),
                                        )
                                        return

                                await asyncio.sleep(0.1)

                        task = asyncio.ensure_future(inner_proxy())
                        await self.allmodules.send_ready_one(
                            instance,
                            no_self_unload=True,
                            from_dlmod=bool(message),
                        )
                        task.cancel()
                    except CoreOverwriteError as e:
                        await core_overwrite(e)
                        return
                    except loader.LoadError as e:
                        with contextlib.suppress(Exception):
                            await self.allmodules.unload_module(
                                instance.__class__.__name__
                            )

                        with contextlib.suppress(Exception):
                            self.allmodules.modules.remove(instance)

                        if message:
                            await utils.answer(
                                message,
                                "<emoji document_id=5454225457916420314>đ</emoji>"
                                f" <b>{utils.escape_html(str(e))}</b>",
                            )
                        return
                    except loader.SelfUnload as e:
                        logger.debug(
                            "Unloading %s, because it raised `SelfUnload`", instance
                        )
                        with contextlib.suppress(Exception):
                            await self.allmodules.unload_module(
                                instance.__class__.__name__
                            )

                        with contextlib.suppress(Exception):
                            self.allmodules.modules.remove(instance)

                        if message:
                            await utils.answer(
                                message,
                                "<emoji document_id=5454225457916420314>đ</emoji>"
                                f" <b>{utils.escape_html(str(e))}</b>",
                            )
                        return
                    except loader.SelfSuspend as e:
                        logger.debug(
                            "Suspending %s, because it raised `SelfSuspend`", instance
                        )
                        if message:
                            await utils.answer(
                                message,
                                "đĨļ <b>Module suspended itself\nReason:"
                                f" {utils.escape_html(str(e))}</b>",
                            )
                        return
                except Exception as e:
                    logger.exception("Module threw because of %s", e)

                    if message is not None:
                        await utils.answer(message, self.strings("load_failed"))

                    return

                instance.hikka_meta_pic = next(
                    (
                        line.replace(" ", "").split("#metapic:", maxsplit=1)[1]
                        for line in doc.splitlines()
                        if line.replace(" ", "").startswith("#metapic:")
                    ),
                    None,
                )

                if is_dragon:
                    instance.name = (
                        "Dragon" + notifier.modname[0].upper() + notifier.modname[1:]
                    )
                    instance.commands = notifier.commands
                    self.allmodules.register_dragon(dragon_module, instance)
                else:
                    for alias, cmd in (
                        self.lookup("settings").get("aliases", {}).items()
                    ):
                        if cmd in instance.commands:
                            self.allmodules.add_alias(alias, cmd)

            try:
                modname = instance.strings("name")
            except (KeyError, AttributeError):
                modname = getattr(instance, "name", "ERROR")

            try:
                developer_entity = await (
                    self._client.force_get_entity
                    if (
                        developer in self._client._hikka_entity_cache
                        and getattr(
                            await self._client.get_entity(developer), "left", True
                        )
                    )
                    else self._client.get_entity
                )(developer)
            except Exception:
                developer_entity = None

            if not isinstance(developer_entity, Channel):
                developer_entity = None


            if message is None:
                return

            modhelp = ""

            if instance.__doc__:
                modhelp += (
                    "<i>\n<emoji document_id=5787544344906959608>âšī¸</emoji>"
                    f" {utils.escape_html(inspect.getdoc(instance))}</i>\n"
                )

            subscribe = ""
            subscribe_markup = None

            depends_from = []
            for key in dir(instance):
                value = getattr(instance, key)
                if isinstance(value, loader.Library):
                    depends_from.append(
                        "<emoji document_id=4971987363145188045>âĢī¸</emoji>"
                        " <code>{}</code> <b>{}</b> <code>{}</code>".format(
                            value.__class__.__name__,
                            self.strings("by"),
                            (
                                value.developer
                                if isinstance(getattr(value, "developer", None), str)
                                else "Unknown"
                            ),
                        )
                    )

            depends_from = (
                self.strings("depends_from").format("\n".join(depends_from))
                if depends_from
                else ""
            )

            def loaded_msg(use_subscribe: bool = True):
                nonlocal modname, version, modhelp, developer, origin, subscribe, blob_link, depends_from
                return self.strings("loaded").format(
                    modname.strip(),
                    version,
                    utils.ascii_face(),
                    modhelp,
                    developer if not subscribe or not use_subscribe else "",
                    depends_from,
                    (
                        self.strings("modlink").format(origin)
                        if origin != "<string>" and self.config["share_link"]
                        else ""
                    ),
                    blob_link,
                    subscribe if use_subscribe else "",
                )

            if developer:
                if developer.startswith("@") and developer not in self.get(
                    "do_not_subscribe", []
                ):
                    if (
                        developer_entity
                        and getattr(developer_entity, "left", True)
                        and self._db.get(main.__name__, "suggest_subscribe", True)
                    ):
                        subscribe = self.strings("suggest_subscribe").format(
                            f"@{utils.escape_html(developer_entity.username)}"
                        )
                        subscribe_markup = [
                            {
                                "text": self.strings("subscribe"),
                                "callback": self._inline__subscribe,
                                "args": (
                                    developer_entity.id,
                                    functools.partial(loaded_msg, use_subscribe=False),
                                    True,
                                ),
                            },
                            {
                                "text": self.strings("no_subscribe"),
                                "callback": self._inline__subscribe,
                                "args": (
                                    developer,
                                    functools.partial(loaded_msg, use_subscribe=False),
                                    False,
                                ),
                            },
                        ]

                developer = self.strings("developer").format(
                    utils.escape_html(developer)
                    if isinstance(developer_entity, Channel)
                    else f"<code>{utils.escape_html(developer)}</code>"
                )
            else:
                developer = ""

            if any(
                line.replace(" ", "") == "#scope:disable_onload_docs"
                for line in doc.splitlines()
            ):
                await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
                return

            for _name, fun in sorted(
                instance.commands.items(),
                key=lambda x: x[0],
            ):
                modhelp += "\n{} <code>{}{}</code> {}".format(
                    (
                        dragon.DRAGON_EMOJI
                        if is_dragon
                        else "<emoji document_id=4971987363145188045>âĢī¸</emoji>"
                    ),
                    self.get_prefix("dragon" if is_dragon else None),
                    _name,
                    (
                        utils.escape_html(fun)
                        if is_dragon
                        else (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings("undoc")
                        )
                    ),
                )

            if self.inline.init_complete and not is_dragon:
                for _name, fun in sorted(
                    instance.inline_handlers.items(),
                    key=lambda x: x[0],
                ):
                    modhelp += self.strings("ihandler").format(
                        f"@{self.inline.bot_username} {_name}",
                        (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings("undoc")
                        ),
                    )

            try:
                await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
            except telethon.errors.rpcerrorlist.MediaCaptionTooLongError:
                await message.reply(loaded_msg(False))

    async def _inline__subscribe(
        self,
        call: InlineCall,
        entity: int,
        msg: typing.Callable[[], str],
        subscribe: bool,
    ):
        if not subscribe:
            self.set("do_not_subscribe", self.get("do_not_subscribe", []) + [entity])
            await utils.answer(call, msg())
            await call.answer(self.strings("not_subscribed"))
            return

        await self._client(JoinChannelRequest(entity))
        await utils.answer(call, msg())
        await call.answer(self.strings("subscribed"))

    @loader.owner
    @loader.command(
        ru_doc="ĐŅĐŗŅŅĐˇĐ¸ŅŅ ĐŧĐžĐ´ŅĐģŅ",
        it_doc="Scarica il modulo",
        de_doc="EntlÃ¤dt ein Modul",
        tr_doc="Bir modÃŧlÃŧ kaldÄąrÄąr",
        uz_doc="Modulni o'chirish",
        es_doc="Descargar el mÃŗdulo",
        kk_doc="ĐĐžĐ´ŅĐģŅĐ´Ņ ĐļĐžŅ",
    )
    async def unloadmod(self, message: Message):
        """Unload module by class name"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("no_class"))
            return

        instance = self.lookup(args, include_dragon=True)

        if issubclass(instance.__class__, loader.Library):
            await utils.answer(message, self.strings("cannot_unload_lib"))
            return

        is_dragon = isinstance(instance, DragonModule)

        if is_dragon:
            worked = [instance.name] if self.allmodules.unload_dragon(instance) else []
        else:
            try:
                worked = await self.allmodules.unload_module(args)
            except CoreUnloadError as e:
                await utils.answer(
                    message,
                    self.strings("unload_core").format(e.module),
                )
                return

        if not self.allmodules.secure_boot:
            self.set(
                "loaded_modules",
                {
                    mod: link
                    for mod, link in self.get("loaded_modules", {}).items()
                    if mod not in worked
                },
            )

        msg = (
            self.strings("unloaded").format(
                dragon.DRAGON_EMOJI
                if is_dragon
                else "<emoji document_id=5784993237412351403>â</emoji>",
                ", ".join(
                    [(mod[:-3] if mod.endswith("Mod") else mod) for mod in worked]
                ),
            )
            if worked
            else self.strings("not_unloaded")
        )

        await utils.answer(message, msg)

    @loader.owner
    @loader.command(
        ru_doc="ĐŖĐ´Đ°ĐģĐ¸ŅŅ Đ˛ŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸",
        it_doc="Rimuovi tutti i moduli",
        de_doc="Entfernt alle Module",
        tr_doc="TÃŧm modÃŧlleri kaldÄąrÄąr",
        uz_doc="Barcha modullarni o'chirish",
        es_doc="Eliminar todos los mÃŗdulos",
        kk_doc="ĐĐ°ŅĐģŅŌ ĐŧĐžĐ´ŅĐģŅĐ´Ņ ĐļĐžŅ",
    )
    async def clearmodules(self, message: Message):
        """Delete all installed modules"""
        await self.inline.form(
            self.strings("confirm_clearmodules"),
            message,
            reply_markup=[
                {
                    "text": self.strings("clearmodules"),
                    "callback": self._inline__clearmodules,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    @loader.command(
        ru_doc="ĐĐžĐąĐ°Đ˛Đ¸ŅŅ Đ´ĐžĐŋĐžĐģĐŊĐ¸ŅĐĩĐģŅĐŊŅĐš ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš",
        it_doc="Aggiungi un repository aggiuntivo",
        de_doc="FÃŧgt ein zusÃ¤tzliches Repository hinzu",
        tr_doc="Ek bir depo ekler",
        uz_doc="Qo'shimcha repozitoriyani qo'shish",
        es_doc="AÃąadir un repositorio adicional",
        kk_doc="ŌĐžŅŅĐŧŅĐ° ŌĐžĐšŅĐŧĐ´ŅŌ ŌĐžŅŅ",
    )
    async def addrepo(self, message: Message):
        """Add a repository to the list of repositories"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_repo"))
            return

        if args in self.config["ADDITIONAL_REPOS"]:
            await utils.answer(message, self.strings("repo_exists"))
            return

        self.config["ADDITIONAL_REPOS"].value = self.config["ADDITIONAL_REPOS"] + [args]

        await utils.answer(message, self.strings("repo_added").format(args))

    @loader.command(
        ru_doc="ĐŖĐ´Đ°ĐģĐ¸ŅŅ Đ´ĐžĐŋĐžĐģĐŊĐ¸ŅĐĩĐģŅĐŊŅĐš ŅĐĩĐŋĐžĐˇĐ¸ŅĐžŅĐ¸Đš",
        it_doc="Rimuovi un repository aggiuntivo",
        de_doc="Entfernt ein zusÃ¤tzliches Repository",
        tr_doc="Ek bir depoyu kaldÄąrÄąr",
        uz_doc="Qo'shimcha repozitoriyani o'chirish",
        es_doc="Eliminar un repositorio adicional",
        kk_doc="ŌĐžŅŅĐŧŅĐ° ŌĐžĐšŅĐŧĐ´ŅŌŅŅ ĐļĐžŅ",
    )
    async def delrepo(self, message: Message):
        """Remove a repository from the list of repositories"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_repo"))
            return

        if args not in self.config["ADDITIONAL_REPOS"]:
            await utils.answer(message, self.strings("repo_not_exists"))
            return

        self.config["ADDITIONAL_REPOS"].value = [
            repo for repo in self.config["ADDITIONAL_REPOS"] if repo != args
        ]

        await utils.answer(message, self.strings("repo_deleted").format(args))

    async def _inline__clearmodules(self, call: InlineCall):
        self.set("loaded_modules", {})

        for file in os.scandir(loader.LOADED_MODULES_DIR):
            try:
                shutil.rmtree(file.path)
            except Exception:
                logger.debug("Failed to remove %s", file.path, exc_info=True)

        self.set("chosen_preset", "none")

        await utils.answer(call, self.strings("all_modules_deleted"))
        await self.lookup("Updater").restart_common(call)

    async def _update_modules(self):
        todo = await self._get_modules_to_load()

        self._secure_boot = False

        if self._db.get(loader.__name__, "secure_boot", False):
            self._db.set(loader.__name__, "secure_boot", False)
            self._secure_boot = True
        else:
            for mod in todo.values():
                await self.download_and_install(mod)

            self.update_modules_in_db()

            aliases = {
                alias: cmd
                for alias, cmd in self.lookup("settings").get("aliases", {}).items()
                if self.allmodules.add_alias(alias, cmd)
            }

            self.lookup("settings").set("aliases", aliases)

        self.fully_loaded = True

        with contextlib.suppress(AttributeError):
            await self.lookup("Updater").full_restart_complete(self._secure_boot)

    async def reload_core(self) -> int:
        """Forcefully reload all core modules"""
        self.fully_loaded = False

        if self._secure_boot:
            self._db.set(loader.__name__, "secure_boot", True)

        for module in self.allmodules.modules:
            if module.__origin__.startswith("<core"):
                module.__origin__ = "<reload-core>"

        loaded = await self.allmodules.register_all(no_external=True)
        for instance in loaded:
            self.allmodules.send_config_one(instance)
            await self.allmodules.send_ready_one(
                instance,
                no_self_unload=False,
                from_dlmod=False,
            )

        self.fully_loaded = True
        return len(loaded)
