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

    @tag.subcommand(name="newtag", help="Create new tag-group. !tag newgroup <tagname>")
    @command.argument("tag", pass_raw=True, required=True)
    async def new_tag(self, evt: MessageEvent, tag: str):
        if self.db.insert_new_tag(tag, evt.room_id):
            message = 'New tag has been created'
        else:
            message = 'Tag does already exist'
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{message}")
        await self.client.send_message(evt.room_id, content)

    @tag.subcommand(name="adduser", aliases="addusr",
                    help="Add a user that will be tagged when using specified tag. !tag adduser <tagname> <userid>")
    @command.argument("tag", required=True)
    @command.argument("user_id", required=True)
    async def add_user_to_tag(self, evt: MessageEvent, tag: str, user_id: str):
        if self.db.insert_user_membership(tag, user_id, evt.room_id):
            message_html = f"User <a href='https://matrix.to/#/{user_id}'>{user_id}</a> added to tag group {tag} in <a href='https://matrix.to/#/{evt.room_id}'>{evt.room_id}</a>."
            message = f"User [{user_id}](https://matrix.to/#/{user_id}) added to tag group {tag} in [{evt.room_id}](https://matrix.to/#/{evt.room_id})."
        else:
            message_html = f"User <a href='https://matrix.to/#/{user_id}'>{user_id}</a> already belong to tag group {tag} in <a href='https://matrix.to/#/{evt.room_id}'>{evt.room_id}</a>."
            message = f"User [{user_id}](https://matrix.to/#/{user_id}) already belong to tag group {tag} in [{evt.room_id}](https://matrix.to/#/{evt.room_id})."
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{message}", format=Format.HTML, formatted_body=f"{message_html}")
        await self.client.send_message(evt.room_id, content)
        return

    @tag.subcommand(name="deluser", aliases="delusr", help="Remove a player from a tag-group !tag deluser <tagname> <userid>")
    @command.argument("tag", required=True)
    @command.argument("user_id", required=True)
    async def del_user_from_tag(self, evt: MessageEvent, tag: str, user_id: str):
        if self.db.remove_user_from_group_byt_tag(tag, user_id, evt.room_id):
            message_html = f"User <a href='https://matrix.to/#/{user_id}'>{user_id}</a> removed from tag group {tag} in <a href='https://matrix.to/#/{evt.room_id}'>{evt.room_id}</a>."
            message = f"User [{user_id}](https://matrix.to/#/{user_id}) removed from tag group {tag} in [{evt.room_id}](https://matrix.to/#/{evt.room_id})."
        else:
            message_html = f"User <a href='https://matrix.to/#/{user_id}'>{user_id}</a> is not a member of tag group {tag} in <a href='https://matrix.to/#/{evt.room_id}'>{evt.room_id}</a>."
            message = f"User [{user_id}](https://matrix.to/#/{user_id}) is not a member of tag group {tag} in [{evt.room_id}](https://matrix.to/#/{evt.room_id})."
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{message}", format=Format.HTML,
                                          formatted_body=f"{message_html}")
        await self.client.send_message(evt.room_id, content)
        return

    async def everyone(self, evt: MessageEvent, message: str = '') -> None:
        members = await self.client.get_members(evt.room_id)
        botUid = await self.client.whoami()
        users_html = ""
        users = ""
        added_members = []
        for member in members:
            if member.sender != botUid and member.sender not in added_members:
                users_html += f" <a href='https://matrix.to/#/{member.sender}'>{member.sender}</a> "
                users += f" [{member.sender}](https://matrix.to/#/{member.sender}) "
                added_members.append(member.sender)
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{users} \n {message}", format=Format.HTML,
                                          formatted_body=f"{users_html} \n {message}")
        await self.client.send_message(evt.room_id, content)

    @command.passive("^@")
    async def tag_everyone(self, evt: MessageEvent, match: Tuple[str]):
        message = ''
        rcv_msg = re.split(r"\s", match[0], 1, re.I)
        tag = rcv_msg[0].lower()
        if len(rcv_msg) > 1:
            message = rcv_msg[1]
        if tag == "@everyone" or tag == "@here":
            await self.everyone(evt, message=message)
            return
        else:
            registered_tags = self.db.get_all_tags()
            for reg_tag in registered_tags:
                if tag == "@" + reg_tag.lower():
                    members = self.db.get_members_of_group_by_tag(reg_tag, evt.room_id)
                    users = ''
                    users_html = ''
                    added_users = []
                    for member in members:
                        if member not in added_users:
                            users_html += f" <a href='https://matrix.to/#/{member}'>{member}</a> "
                            users += f" [{member}](https://matrix.to/#/{member}) "
                            added_users.append(member)
                    content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{users} \n {message}",
                                                      format=Format.HTML, formatted_body=f"{users_html} \n {message}")
                    await self.client.send_message(evt.room_id, content)
                    return

