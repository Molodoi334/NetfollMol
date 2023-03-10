# ÂŠī¸ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# đ https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# đ https://www.gnu.org/licenses/agpl-3.0.html
# Netfoll Team modifided Hikka files for Netfoll
# đ https://github.com/MXRRI/Netfoll

import logging
import os
from random import choice

from .. import loader, translations, utils
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)

imgs = [
    "https://i.gifer.com/Erie.gif",
    "https://i.gifer.com/QD5k.gif",
    "https://i.gifer.com/ZAAd.gif",
    "https://i.gifer.com/KmhC.gif",
]


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    strings = {
        "name": "Quickstart",
        "base": """đđģ <b>Hi!</b> I am a <B> inline-bot Netfoll</B>, then let's go through a little training and configure Netfoll for your needs

đ¤đģ <b>We advise you to join </b><a href="https://t.me/NetfollUB "><b>our chat!</b></a><b> There you can find help if you don't understand something or if there are problems

</b> âĄī¸ <b>You can search for interesting modules using </b>@hikkamods_bot<b>, use it as a built-in installation on the required module.
</b> đĨ <i>You can find channels of confirmed developers can be found </i><a href="https://t.me/NetfollUB/279 "><I> am here

</i></a> đ¯ <b>A brief guide</b>:

<i> đ¸ In order to find out the modules installed on you, use .mods
đš To install the module from the file, use </i> <code>.lm</code><i> (</i><code>.loadmod</code><i>) and to delete </i>.unloadmod
<i> đē More usage guides can be found in the chat </i><a href="https://t.me/NetfollUB/3373 ">Netfoll

</a><i> đ¤ <b>Netfoll</b> is based on <b>Hikka</b>, therefore supports modules <b>Hikka</b>, <b>FTG</b>, <b>DragonUB</b> and <b>GeekTG</b> and their own.</i>""",
        "railway": (
            "đ <b>Your userbot is installed on Railway</b>. This platform has only"
            " <b>500 free hours per month</b>. Once this limit is reached, your"
            " <b>Hikka will be frozen</b>. Next month <b>you will need to go to"
            " https://railway.app and restart it</b>."
        ),
        "language_saved": "đŦđ§ Language saved!",
        "language": "đŦđ§ English",
        "btn_support": "đž Netfoll Chat",
    }

    strings_ru = {
        "base": """đđģ <b>ĐŅĐ¸Đ˛ĐĩŅ!</b> Đ¯ ŅĐ˛ĐģŅŅŅŅ<b> Inline-ĐąĐžŅĐžĐŧ Netfoll</b>, Đ´Đ°Đ˛Đ°Đš ĐŋŅĐžĐšĐ´ĐĩĐŧ ĐŊĐĩĐąĐžĐģŅŅĐžĐĩ ĐžĐąŅŅĐĩĐŊĐ¸Đĩ Đ¸ ĐŊĐ°ŅŅŅĐžĐ¸Đŧ Netfoll ĐŋĐžĐ´ ŅĐ˛ĐžĐ¸ ĐŊŅĐļĐ´Ņ 

đ¤đģ <b>ĐĄĐžĐ˛ĐĩŅŅĐĩĐŧ Đ˛ŅŅŅĐŋĐ¸ŅŅ Đ˛ </b><a href="https://t.me/NetfollUB"><b>ĐŊĐ°Ņ ŅĐ°Ņ!</b></a><b> ĐĸĐ°Đŧ Đ˛Ņ ŅĐŧĐžĐļĐĩŅĐĩ ĐŊĐ°ĐšŅĐ¸ ĐŋĐžĐŧĐžŅŅ ĐĩŅĐģĐ¸ ŅĐĩĐŗĐž ŅĐž ĐŊĐĩ ĐŋĐžĐšĐŧĐĩŅĐĩ Đ¸ĐģĐ¸ ĐĩŅĐģĐ¸ ĐąŅĐ´ŅŅ ĐŋŅĐžĐąĐģĐĩĐŧŅ

</b>âĄī¸ <b>ĐŅĐēĐ°ŅŅ Đ¸ĐŊŅĐĩŅĐĩŅĐŊŅĐĩ ĐŧĐžĐ´ŅĐģĐ¸ ĐŧĐžĐļĐŊĐž Ņ ĐŋĐžĐŧĐžŅŅŅ </b>@hikkamods_bot<b>, Đ¸ŅĐŋĐžĐģŅĐˇŅĐšŅĐĩ ĐĩĐŗĐž ĐēĐ°Đē inline Đ¸ĐģĐ¸ ĐēĐ°Đē ĐžĐąŅŅĐŊĐžĐŗĐž ĐąĐžŅĐ° Đ¸ Đ´ĐģŅ ŅŅŅĐ°ĐŊĐžĐ˛ĐēĐ¸ ĐŊĐ°ĐļĐŧĐ¸ŅĐĩ âŠ Install ĐŊĐ° ŅŅĐĩĐąŅĐĩĐŧĐžĐŧ ĐŧĐžĐ´ŅĐģĐĩ. 
</b>đĨ <i>ĐŅ ĐŧĐžĐļĐĩŅĐĩ ĐŊĐ°ĐšŅĐ¸ ĐēĐ°ĐŊĐ°ĐģŅ ĐŋĐžĐ´ŅĐ˛ĐĩŅĐļĐ´ŅĐŊĐŊŅŅ ŅĐ°ĐˇŅĐ°ĐąĐžŅŅĐ¸ĐēĐžĐ˛ ĐŧĐžĐļĐŊĐž ĐŊĐ°ĐšŅĐ¸ </i><a href="https://t.me/NetfollUB/279"><i>ŅŅŅ

</i></a>đ¯ <b>ĐŅĐ°ŅĐēĐ¸Đš ĐŗĐ°ĐšĐ´</b>:

<i>đ¸ ĐĐģŅ ŅĐžĐŗĐž ŅŅĐžĐąŅ ŅĐˇĐŊĐ°ŅŅ ĐŧĐžĐ´ŅĐģĐ¸ ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊĐŊŅĐĩ Ņ Đ˛Đ°Ņ Đ¸ŅĐŋĐžĐģŅĐˇŅĐš .mods
đš ĐĐģŅ ŅŅŅĐ°ĐŊĐžĐ˛ĐēĐ¸ ĐŧĐžĐ´ŅĐģŅ Ņ ŅĐ°ĐšĐģĐ° Đ¸ŅĐŋĐžĐģŅĐˇŅĐš</i> <code>.lm</code><i> (</i><code>.loadmod</code><i>) Đ° Đ´ĐģŅ ŅĐ´Đ°ĐģĐĩĐŊĐ¸Ņ </i>.unloadmod
<i>đē ĐĐžĐģŅŅĐĩ ĐŗĐ°ĐšĐ´ĐžĐ˛ ĐŋĐž Đ¸ŅĐŋĐžĐģŅĐˇĐžĐ˛Đ°ĐŊĐ¸Ņ ĐŧĐžĐļĐĩŅĐĩ ĐŊĐ°ĐšŅĐ¸ Đ˛ ŅĐ°ŅĐĩ </i><a href="https://t.me/NetfollUB/3373">Netfoll

</a><i>đ¤ <b>Netfoll</b> ĐžŅĐŊĐžĐ˛Đ°ĐŊ ĐŊĐ° <b>Hikka</b>, ĐŋĐžŅŅĐžĐŧŅ ĐŋĐžĐ´Đ´ĐĩŅĐļĐ¸Đ˛Đ°ĐĩŅ ĐŧĐžĐ´ŅĐģĐ¸ <b>Hikka</b>, <b>FTG</b>, <b>DragonUB</b> Đ¸ <b>GeekTG</b> Đ¸ ŅĐ˛ĐžĐ¸ ŅĐžĐąŅŅĐ˛ĐĩĐŊĐŊŅĐĩ.</i>
""",
        "railway": (
            "đ <b>ĐĸĐ˛ĐžĐš ŅĐˇĐĩŅĐąĐžŅ ŅŅŅĐ°ĐŊĐžĐ˛ĐģĐĩĐŊ ĐŊĐ° Railway</b>. ĐĐ° ŅŅĐžĐš ĐŋĐģĐ°ŅŅĐžŅĐŧĐĩ ŅŅ"
            " ĐŋĐžĐģŅŅĐ°ĐĩŅŅ ŅĐžĐģŅĐēĐž <b>500 ĐąĐĩŅĐŋĐģĐ°ŅĐŊŅŅ ŅĐ°ŅĐžĐ˛ Đ˛ ĐŧĐĩŅŅŅ</b>. ĐĐžĐŗĐ´Đ° ĐģĐ¸ĐŧĐ¸Ņ ĐąŅĐ´ĐĩŅ"
            " Đ´ĐžŅŅĐ¸ĐŗĐŊĐĩŅ, ŅĐ˛ĐžĐš <b>ŅĐˇĐĩŅĐąĐžŅ ĐąŅĐ´ĐĩŅ ĐˇĐ°ĐŧĐžŅĐžĐļĐĩĐŊ</b>. Đ ŅĐģĐĩĐ´ŅŅŅĐĩĐŧ ĐŧĐĩŅŅŅĐĩ <b>ŅŅ"
            " Đ´ĐžĐģĐļĐĩĐŊ ĐąŅĐ´ĐĩŅŅ ĐŋĐĩŅĐĩĐšŅĐ¸ ĐŊĐ° https://railway.app Đ¸ ĐŋĐĩŅĐĩĐˇĐ°ĐŋŅŅŅĐ¸ŅŅ ĐĩĐŗĐž</b>."
        ),
        "language_saved": "đˇđē Đ¯ĐˇŅĐē ŅĐžŅŅĐ°ĐŊĐĩĐŊ!",
        "language": "đˇđē Đ ŅŅŅĐēĐ¸Đš",
        "btn_support": "đž Đ§Đ°Ņ Netfoll",
    }

    async def client_ready(self):
        if self.get("disable_quickstart"):
            raise loader.SelfUnload

        self.mark = (
            lambda: [
                [
                    {
                        "text": self.strings("btn_support"),
                        "url": "https://t.me/netfollub",
                    }
                ],
            ]
            + [
                [
                    {
                        "text": "đŠââī¸ Privacy Policy",
                        "url": "https://docs.google.com/document/d/15m6-pb1Eya8Zn4y0_7JEdvMLAo_v050rFMaWrjDjvMs/edit?usp=sharing",
                    },
                    {
                        "text": "đ EULA",
                        "url": "https://docs.google.com/document/d/1sZBk24SWLBLoGxcsZHW8yP7yLncToPGUP1FJ4dS6z5I/edit?usp=sharing",
                    },
                ]
            ]
            + utils.chunks(
                [
                    {
                        "text": (
                            getattr(self, f"strings_{lang}")
                            if lang != "en"
                            else self.strings._base_strings
                        )["language"],
                        "callback": self._change_lang,
                        "args": (lang,),
                    }
                    for lang in [
                        "en",
                        "ru",
                    ]
                ],
                2,
            )
        )

        self.text = lambda: self.strings("base") + (
            self.strings("railway") if "RAILWAY" in os.environ else ""
        )

        await self.inline.bot.send_animation(self._client.tg_id, animation=choice(imgs))
        await self.inline.bot.send_message(
            self._client.tg_id,
            self.text(),
            reply_markup=self.inline.generate_markup(self.mark()),
            disable_web_page_preview=True,
        )

        self.set("disable_quickstart", True)

    async def _change_lang(self, call: BotInlineCall, lang: str):
        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.answer(self.strings("language_saved"))
        await call.edit(text=self.text(), reply_markup=self.mark())
