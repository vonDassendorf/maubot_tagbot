from maubot import Plugin, MessageEvent
from maubot.handlers import command
from mautrix.types import MessageType, TextMessageEventContent, Format
from .database import TagDatabase
from typing import Tuple
import re


class TagBot(Plugin):
    db: TagDatabase

    async def start(self) -> None:
        await super().start()
        self.db = TagDatabase(db=self.database, bot=self)

    @command.new(name="tag", require_subcommand=True, help="Configure tags")
    async def tag(self):
        pass

    @tag.subcommand(name="newtag", help="Create new group. !tag newgroup <tagname>")
    @command.argument("tag", pass_raw=True, required=True)
    async def new_tag(self, evt: MessageEvent, tag: str):
        if self.db.insert_new_tag(tag, evt.room_id):
            message = 'New tag has been created'
        else:
            message = 'Tag does already exist'
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{message}")
        await self.client.send_message(evt.room_id, content)

    @tag.subcommand(name="adduser", aliases="addusr", help="Add a user that will be tagged when using specified tag. !tag adduser <tagname> <userid>")
    @command.argument("args", pass_raw=True, required=True)
    async def add_user_to_tag(self, evt: MessageEvent, args: str):
        args = args.split(' ')
        tag = args.pop(0)
        self.log.info(args)
        for arg in args:
            user_id = arg
            if self.db.insert_user_membership(tag, user_id):
                message = f"User {user_id} added to tag group {tag}."
            else:
                message = f"User {user_id} already belong to tag group {tag}."
            content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{message}")
            await self.client.send_message(evt.room_id, content)
        return

    async def everyone(self, evt: MessageEvent, message: str = '') -> None:
        members = await self.client.get_members(evt.room_id)
        botUid = await self.client.whoami()
        users_html = ""
        users = ""
        for member in members:
            if member.sender != botUid:
                users_html += f" <a href='https://matrix.to/#/{member.sender}'>{member.sender}</a> "
                users += f" [{member.sender}](https://matrix.to/#/{member.sender}) "
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{users} {message}", format=Format.HTML, formatted_body=f"{users_html} {message}")
        await self.client.send_message(evt.room_id, content)

    @command.passive("^@")
    @command.argument('message', pass_raw=True, required=False)
    async def tag_everyone(self, evt: MessageEvent, match: Tuple[str], message: str = ''):
        if match[0].startswith("@everyone"):
            await self.everyone(evt, message=message)
            return
        else:
            registered_tags = self.db.get_all_tags()
            for reg_tag in registered_tags:
                if match[0].startswith("@"+reg_tag):
                    members = self.db.get_members_of_group_by_tag(reg_tag)
                    users = ''
                    users_html = ''
                    for member in members:
                        users_html += f" <a href='https://matrix.to/#/{member}'>{member}</a> "
                        users += f" [{member}](https://matrix.to/#/{member}) "
                    content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{users} {message}",
                                                      format=Format.HTML, formatted_body=f"{users_html} {message}")
                    await self.client.send_message(evt.room_id, content)
                    return
