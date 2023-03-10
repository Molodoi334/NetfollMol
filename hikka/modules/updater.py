# ÂŠī¸ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# đ https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# đ https://www.gnu.org/licenses/agpl-3.0.html
# Netfoll Team modifided Hikka files for Netfoll
# đ https://github.com/MXRRI/Netfoll

import asyncio
import contextlib
import logging
import os
import subprocess
import sys
import time
import typing

import git
from git import GitCommandError, Repo
from telethon.extensions.html import CUSTOM_EMOJIS
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import DialogFilter, Message

from .. import loader, main, utils, version
from .._internal import restart
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Updates itself"""

    strings = {
        "name": "Updater",
        "source": (
            "<emoji document_id=5456255401194429832>đ</emoji> <b>Read the source code"
            " from</b> <a href='{}'>here</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=5325792861885570739>đ</emoji> <b>Your {} is"
            " restarting...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>đ</emoji> <b>Downloading"
            " updates...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>đ</emoji> <b>Installing"
            " updates...</b>"
        ),
        "success": (
            "<emoji document_id=5305683825005700455>đ</emoji> <b>Restart successful!"
            " {}</b>\n<i>Loading modules...</i>\n<i>Restart took {}s</i>"
        ),
        "origin_cfg_doc": "Git origin URL, for where to update from",
        "btn_restart": "đ Restart",
        "btn_update": "đ§­ Update",
        "restart_confirm": "â <b>Are you sure you want to restart?</b>",
        "secure_boot_confirm": (
            "â <b>Are you sure you want to restart in secure boot mode?</b>"
        ),
        "update_confirm": (
            "â <b>Are you sure you"
            " want to update?\n\n<a"
            ' href="https://github.com/MXRRI/Netfoll/{}">{}</a> â¤ <a'
            ' href="https://github.com/MXRRI/Netfoll/{}">{}</a></b>'
        ),
        "no_update": "đ¸ <b>You are on the latest version, pull updates anyway?</b>",
        "cancel": "đĢ Cancel",
        "lumihost_restart": (
            "<b>Your {} is"
            " restarting...</b>"
        ),
        "lumihost_update": (
            "<b>Your {} is"
            " updating...</b>"
        ),
        "full_success": (
            "<emoji document_id=5348526883992510786>đ</emoji> <b>Userbot ready"
            " to use! {}</b>\n<i>Full restart took {}s</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>đ</emoji> <b>Secure boot completed!"
            " {}</b>\n<i>Restart took {}s</i>"
        ),
    }

    strings_ru = {
        "source": (
            "<emoji document_id=5456255401194429832>đ</emoji> <b>ĐŅŅĐžĐ´ĐŊŅĐš ĐēĐžĐ´ ĐŧĐžĐļĐŊĐž"
            " ĐŋŅĐžŅĐ¸ŅĐ°ŅŅ</b> <a href='{}'>ĐˇĐ´ĐĩŅŅ</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=5325792861885570739>đ</emoji> <b>ĐĸĐ˛ĐžĐš {}"
            " ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐļĐ°ĐĩŅŅŅ...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>đ</emoji> <b>ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐŊĐ¸Đĩ"
            " ĐžĐąĐŊĐžĐ˛ĐģĐĩĐŊĐ¸Đš...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>đ</emoji> <b>ĐŖŅŅĐ°ĐŊĐžĐ˛ĐēĐ°"
            " ĐžĐąĐŊĐžĐ˛ĐģĐĩĐŊĐ¸Đš...</b>"
        ),
        "success": (
            "<emoji document_id=5305683825005700455>đ</emoji> <b>ĐĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐ°"
            " ŅŅĐŋĐĩŅĐŊĐ°! {}</b>\n<i>ĐĐ´ĐĩŅ ĐŋŅĐžŅĐĩŅŅ ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸ ĐŧĐžĐ´ŅĐģĐĩĐš...</i>\n<i>ĐĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐ°"
            " Đ´ĐģĐ¸ĐģĐ°ŅŅ {} ŅĐĩĐē</i>"
        ),
        "full_success": (
            "<emoji document_id=5348526883992510786>đ</emoji> <b>ĐŽĐˇĐĩŅĐąĐžŅ ĐŗĐžŅĐžĐ˛ Đē"
            " ŅĐ°ĐąĐžŅĐĩ! {}</b>\n<i>ĐĐžĐģĐŊĐ°Ņ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐ° ĐˇĐ°ĐŊŅĐģĐ° {} ŅĐĩĐē</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>đ</emoji> <b>ĐĐĩĐˇĐžĐŋĐ°ŅĐŊĐ°Ņ ĐˇĐ°ĐŗŅŅĐˇĐēĐ°"
            " ĐˇĐ°Đ˛ĐĩŅŅĐĩĐŊĐ°! {}</b>\n<i>ĐĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐēĐ° ĐˇĐ°ĐŊŅĐģĐ° {} ŅĐĩĐē</i>"
        ),
        "origin_cfg_doc": "ĐĄŅŅĐģĐēĐ°, Đ¸Đˇ ĐēĐžŅĐžŅĐžĐš ĐąŅĐ´ŅŅ ĐˇĐ°ĐŗŅŅĐļĐ°ŅŅŅŅ ĐžĐąĐŊĐžĐ˛ĐģĐĩĐŊĐ¸Ņ",
        "btn_restart": "đ ĐĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐ¸ŅŅŅŅ",
        "btn_update": "đ§­ ĐĐąĐŊĐžĐ˛Đ¸ŅŅŅŅ",
        "restart_confirm": "â <b>ĐĸŅ ŅĐ˛ĐĩŅĐĩĐŊ, ŅŅĐž ŅĐžŅĐĩŅŅ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐ¸ŅŅŅŅ?</b>",
        "secure_boot_confirm": (
            "â <b>ĐĸŅ ŅĐ˛ĐĩŅĐĩĐŊ, ŅŅĐž"
            " ŅĐžŅĐĩŅŅ ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐˇĐ¸ŅŅŅŅ Đ˛ ŅĐĩĐļĐ¸ĐŧĐĩ ĐąĐĩĐˇĐžĐŋĐ°ŅĐŊĐžĐš ĐˇĐ°ĐŗŅŅĐˇĐēĐ¸?</b>"
        ),
        "update_confirm": (
            "â <b>ĐĸŅ ŅĐ˛ĐĩŅĐĩĐŊ, ŅŅĐž"
            " ŅĐžŅĐĩŅŅ ĐžĐąĐŊĐžĐ˛Đ¸ŅŅŅŅ??\n\n<a"
            ' href="https://github.com/MXRRI/Netfoll/commit/{}">{}</a> â¤ <a'
            ' href="https://github.com/MXRRI/Netfoll/commit/{}">{}</a></b>'
        ),
        "no_update": "đ¸ <b>ĐŖ ŅĐĩĐąŅ ĐŋĐžŅĐģĐĩĐ´ĐŊŅŅ Đ˛ĐĩŅŅĐ¸Ņ. ĐĐąĐŊĐžĐ˛Đ¸ŅŅŅŅ ĐŋŅĐ¸ĐŊŅĐ´Đ¸ŅĐĩĐģŅĐŊĐž?</b>",
        "cancel": "đĢ ĐŅĐŧĐĩĐŊĐ°",
        "_cls_doc": "ĐĐąĐŊĐžĐ˛ĐģŅĐĩŅ ŅĐˇĐĩŅĐąĐžŅ",
        "lumihost_restart": (
            "<b>ĐĸĐ˛ĐžĐš {}"
            " ĐŋĐĩŅĐĩĐˇĐ°ĐŗŅŅĐļĐ°ĐĩŅŅŅ...</b>"
        ),
        "lumihost_update": (
            "<b>ĐĸĐ˛ĐžĐš {}"
            " ĐžĐąĐŊĐžĐ˛ĐģŅĐĩŅŅŅ...</b>"
        ),
    }

    strings_uk = {
        "source": (
            "<emoji document_id=5456255401194429832>đ</emoji> <b>ĐĐ¸ŅŅĐ´ĐŊĐ¸Đš ĐēĐžĐ´ ĐŧĐžĐļĐŊĐ°"
            " ĐŋŅĐžŅĐ¸ŅĐ°Đ˛ŅĐ¸</b> <a href='{}'>ŅŅŅ</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=5325792861885570739>đ</emoji> <b>ĐĸĐ˛ĐžĐŗĐž {}"
            " ĐŋĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļŅĐ˛Đ°ŅĐ¸...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>đ</emoji> <b>ĐĄĐēĐ°ŅŅĐ˛Đ°ĐŊĐŊŅ"
            " ĐžĐŊĐžĐ˛ĐģĐĩĐŊĐŊŅ...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>đ</emoji> <b>ĐŖŅŅĐ°ĐŊĐžĐ˛ĐēĐ°"
            " ĐžĐŊĐžĐ˛ĐģĐĩĐŊĐŊŅ...</b>"
        ),
        "success": (
            "<emoji document_id=5305683825005700455>đ</emoji> <b>ĐĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ"
            " ŅŅĐŋŅŅĐŊĐ¸Đš! {}</b>\n<i>ĐĐ´Đĩ ĐŋŅĐžŅĐĩŅ ĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ ĐĐžĐ´ŅĐģŅĐ˛...</i>\n<i>ĐĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ"
            " ŅŅĐ¸Đ˛Đ°ŅĐ¸ {} ŅĐĩĐē</i>"
        ),
        "full_success": (
            "<emoji document_id=5348526883992510786>đ</emoji> <b>ĐŽĐˇĐĩŅĐąĐžŅ ĐŗĐžŅĐžĐ˛Đ¸Đš Đ´Đž"
            " ŅĐžĐąĐžŅĐ¸! {}</b>\n<i>ĐĐžĐ˛ĐŊĐĩ ĐŋĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ ĐˇĐ°ĐšĐŊŅĐģĐž {} ŅĐĩĐē</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>đ</emoji> <b>ĐĐĩĐˇĐŋĐĩŅĐŊĐĩ ĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ"
            " ĐˇĐ°Đ˛ĐĩŅŅĐĩĐŊĐ¸Đš! {}</b>\n<i>ĐĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ ĐˇĐ°ĐšĐŊŅĐģĐž {} ŅĐĩĐē</i>"
        ),
        "origin_cfg_doc": "ĐĐžŅĐ¸ĐģĐ°ĐŊĐŊŅ, Đˇ ŅĐēĐžŅ ĐąŅĐ´ŅŅŅ ĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļŅĐ˛Đ°ŅĐ¸ŅŅ ĐžĐŊĐžĐ˛ĐģĐĩĐŊĐŊŅ",
        "btn_restart": "đ ĐĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐ¸ŅĐ¸ŅŅ",
        "btn_update": "đ§­ ĐĐŊĐžĐ˛Đ¸ŅĐ¸ŅŅ",
        "restart_confirm": "â <b>ĐĐ¸ Đ˛ĐŋĐĩĐ˛ĐŊĐĩĐŊŅ, ŅĐž ŅĐžŅĐĩŅĐĩ ĐŋĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐ¸ŅĐ¸ŅŅ?</b>",
        "secure_boot_confirm": (
            "â <b>ĐĸĐ¸ Đ˛ĐŋĐĩĐ˛ĐŊĐĩĐŊĐ¸Đš, ŅĐž"
            " ŅĐžŅĐĩŅ ĐŋĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐ¸ŅĐ¸ŅŅ Đ˛ ŅĐĩĐļĐ¸ĐŧŅ ĐąĐĩĐˇĐŋĐĩŅĐŊĐžĐŗĐž ĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļĐĩĐŊĐŊŅ?</b>"
        ),
        "update_confirm": (
            "â <b>ĐĸĐ¸ Đ˛ĐŋĐĩĐ˛ĐŊĐĩĐŊĐ¸Đš, ŅĐž"
            " ŅĐžŅĐĩŅ ĐžĐŊĐžĐ˛Đ¸ŅĐ¸ŅŅ??\n\n<a"
            ' href="https://github.com/MXRRI/Netfoll/commit/{}">{}</a> â¤ <a'
            ' href="https://github.com/MXRRI/Netfoll/commit/{}">{}</a></b>'
        ),
        "no_update": "đ¸ <b>ĐŖ Đ˛Đ°Ņ ĐžŅŅĐ°ĐŊĐŊŅ Đ˛ĐĩŅŅŅŅ. ĐĐŊĐžĐ˛Đ¸ŅĐ¸ŅŅ ĐŋŅĐ¸ĐŧŅŅĐžĐ˛Đž?</b>",
        "cancel": "đĢ ĐĄĐēĐ°ŅŅĐ˛Đ°ĐŊĐŊŅ",
        "_cls_doc": "ĐĐŊĐžĐ˛ĐģŅŅ ŅĐˇĐĩŅĐąĐžŅ",
        "lumihost_restart": (
            "<b>ĐĸĐ˛ĐžĐŗĐž {}"
            " ĐŋĐĩŅĐĩĐˇĐ°Đ˛Đ°ĐŊŅĐ°ĐļŅĐ˛Đ°ŅĐ¸...</b>"
        ),
        "lumihost_update": (
            "<b>ĐĸĐ˛ĐžĐŗĐž {}"
            " ĐžĐŊĐžĐ˛ĐģŅĐ˛Đ°ŅĐ¸ŅŅ...</b>"
        ),
    }    

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "GIT_ORIGIN_URL",
                "https://github.com/MXRRI/Netfoll",
                lambda: self.strings("origin_cfg_doc"),
                validator=loader.validators.Link(),
            )
        )

    @loader.owner
    @loader.command(ru_doc="ĐĐĩŅĐĩĐˇĐ°ĐŗŅŅĐļĐ°ĐĩŅ ŅĐˇĐĩŅĐąĐžŅ")
    async def restart(self, message: Message):
        """Restarts the userbot"""
        args = utils.get_args_raw(message)
        secure_boot = any(trigger in args for trigger in {"--secure-boot", "-sb"})
        try:
            if (
                "-f" in args
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings(
                        "secure_boot_confirm" if secure_boot else "restart_confirm"
                    ),
                    reply_markup=[
                        {
                            "text": self.strings("btn_restart"),
                            "callback": self.inline_restart,
                            "args": (secure_boot,),
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                )
            ):
                raise
        except Exception:
            await self.restart_common(message, secure_boot)

    async def inline_restart(self, call: InlineCall, secure_boot: bool = False):
        await self.restart_common(call, secure_boot=secure_boot)

    async def process_restart_message(self, msg_obj: typing.Union[InlineCall, Message]):
        self.set(
            "selfupdatemsg",
            msg_obj.inline_message_id
            if hasattr(msg_obj, "inline_message_id")
            else f"{utils.get_chat_id(msg_obj)}:{msg_obj.id}",
        )

    async def restart_common(
        self,
        msg_obj: typing.Union[InlineCall, Message],
        secure_boot: bool = False,
    ):
        if (
            hasattr(msg_obj, "form")
            and isinstance(msg_obj.form, dict)
            and "uid" in msg_obj.form
            and msg_obj.form["uid"] in self.inline._units
            and "message" in self.inline._units[msg_obj.form["uid"]]
        ):
            message = self.inline._units[msg_obj.form["uid"]]["message"]
        else:
            message = msg_obj

        if secure_boot:
            self._db.set(loader.__name__, "secure_boot", True)

        msg_obj = await utils.answer(
            msg_obj,
            self.strings("restarting_caption").format(
                utils.get_platform_emoji(self._client)
                if self._client.hikka_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "<emoji document_id=5364105417569868801>đ</emoji> <b>LumiHost</b>"
            )
            if "LUMIHOST" in os.environ
            else self.strings("lumihost_restart").format(
                '<emoji document_id=5364105417569868801>đ</emoji> <b>LumiHost</b>'
                if self._client.hikka_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "Netfoll"
            ),
        )

        await self.process_restart_message(msg_obj)

        self.set("restart_ts", time.time())

        await self._db.remote_force_save()

        if "LAVHOST" in os.environ:
            os.system("lavhost restart")
            return

        with contextlib.suppress(Exception):
            await main.hikka.web.stop()

        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)

        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()

        await message.client.disconnect()
        restart()

    async def download_common(self):
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            r = origin.pull()
            new_commit = repo.head.commit
            for info in r:
                if info.old_commit:
                    for d in new_commit.diff(info.old_commit):
                        if d.b_path == "requirements.txt":
                            return True
            return False
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)
            return False

    @staticmethod
    def req_common():
        # Now we have downloaded new code, install requirements
        logger.debug("Installing new requirements...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(
                        os.path.dirname(utils.get_base_dir()),
                        "requirements.txt",
                    ),
                    "--user",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.exception("Req install failed")

    @loader.owner
    @loader.command(ru_doc="ĐĄĐēĐ°ŅĐ¸Đ˛Đ°ĐĩŅ ĐžĐąĐŊĐžĐ˛ĐģĐĩĐŊĐ¸Ņ ŅĐˇĐĩŅĐąĐžŅĐ°")
    async def update(self, message: Message):
        """Downloads userbot updates"""
        try:
            args = utils.get_args_raw(message)
            current = utils.get_git_hash()
            upcoming = next(
                git.Repo().iter_commits(f"origin/{version.branch}", max_count=1)
            ).hexsha
            if (
                "-f" in args
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("update_confirm").format(
                        current, current[:8], upcoming, upcoming[:8]
                    )
                    if upcoming != current
                    else self.strings("no_update"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_update"),
                            "callback": self.inline_update,
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                )
            ):
                raise
        except Exception:
            await self.inline_update(message)

    async def inline_update(
        self,
        msg_obj: typing.Union[InlineCall, Message],
        hard: bool = False,
    ):
        # We don't really care about asyncio at this point, as we are shutting down
        if hard:
            os.system(f"cd {utils.get_base_dir()} && cd .. && git reset --hard HEAD")

        try:
            if "" in os.environ:
                await self.process_restart_message(msg_obj)
                return

            with contextlib.suppress(Exception):
                msg_obj = await utils.answer(msg_obj, self.strings("downloading"))

            req_update = await self.download_common()

            with contextlib.suppress(Exception):
                msg_obj = await utils.answer(msg_obj, self.strings("installing"))

            if req_update:
                self.req_common()

            await self.restart_common(msg_obj)
        except GitCommandError:
            if not hard:
                await self.inline_update(msg_obj, True)
                return

            logger.critical("Got update loop. Update manually via .terminal")

    @loader.unrestricted
    @loader.command(ru_doc="ĐĐžĐēĐ°ĐˇĐ°ŅŅ ŅŅŅĐģĐēŅ ĐŊĐ° Đ¸ŅŅĐžĐ´ĐŊŅĐš ĐēĐžĐ´ ĐŋŅĐžĐĩĐēŅĐ°")
    async def source(self, message: Message):
        """Links the source code of this project"""
        await utils.answer(
            message,
            self.strings("source").format(self.config["GIT_ORIGIN_URL"]),
        )

    async def client_ready(self):
        if self.get("selfupdatemsg") is not None:
            try:
                await self.update_complete()
            except Exception:
                logger.exception("Failed to complete update!")

        if self.get("do_not_create", False):
            return

        try:
            await self._add_folder()
        except Exception:
            logger.exception("Failed to add folder!")

        self.set("do_not_create", True)

    async def _add_folder(self):
        folders = await self._client(GetDialogFiltersRequest())

        if any(getattr(folder, "title", None) == "hikka" for folder in folders):
            return

        try:
            folder_id = (
                max(
                    folders,
                    key=lambda x: x.id,
                ).id
                + 1
            )
        except ValueError:
            folder_id = 2

        try:
            await self._client(
                UpdateDialogFilterRequest(
                    folder_id,
                    DialogFilter(
                        folder_id,
                        title="hikka",
                        pinned_peers=(
                            [
                                await self._client.get_input_entity(
                                    self._client.loader.inline.bot_id
                                )
                            ]
                            if self._client.loader.inline.init_complete
                            else []
                        ),
                        include_peers=[
                            await self._client.get_input_entity(dialog.entity)
                            async for dialog in self._client.iter_dialogs(
                                None,
                                ignore_migrated=True,
                            )
                            if dialog.name
                            in {
                                "netfoll-logs",
                                "netfoll-onload",
                                "netfoll-assets",
                                "netfoll-backups",
                                "netfoll-acc-switcher",
                                "silent-tags",
                            }
                            and dialog.is_channel
                            and (
                                dialog.entity.participants_count == 1
                                or dialog.entity.participants_count == 2
                                and dialog.name in {"netfoll-logs", "silent-tags"}
                            )
                            or (
                                self._client.loader.inline.init_complete
                                and dialog.entity.id
                                == self._client.loader.inline.bot_id
                            )
                            or dialog.entity.id
                            in [
                                1554874075,
                                1697279580,
                                1679998924,
                            ]  # official hikka chats
                        ],
                        emoticon="đą",
                        exclude_peers=[],
                        contacts=False,
                        non_contacts=False,
                        groups=False,
                        broadcasts=False,
                        bots=False,
                        exclude_muted=False,
                        exclude_read=False,
                        exclude_archived=False,
                    ),
                )
            )
        except Exception:
            logger.critical(
                "Can't create Netfoll folder. Possible reasons are:\n"
                "- User reached the limit of folders in Telegram\n"
                "- User got floodwait\n"
                "Ignoring error and adding folder addition to ignore list"
            )

    async def update_complete(self):
        logger.debug("Self update successful! Edit message")
        start = self.get("restart_ts")
        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        msg = self.strings("success").format(utils.ascii_face(), took)
        ms = self.get("selfupdatemsg")

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=self.inline.sanitise_text(msg),
        )

    async def full_restart_complete(self, secure_boot: bool = False):
        start = self.get("restart_ts")

        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        self.set("restart_ts", None)

        ms = self.get("selfupdatemsg")
        msg = self.strings(
            "secure_boot_complete" if secure_boot else "full_success"
        ).format(utils.ascii_face(), took)

        if ms is None:
            return

        self.set("selfupdatemsg", None)

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            await asyncio.sleep(60)
            await self._client.delete_messages(chat_id, message_id)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=self.inline.sanitise_text(msg),
        )