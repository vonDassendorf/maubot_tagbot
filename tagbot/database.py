from sqlalchemy import (Column, String, Integer, Text, ForeignKey, UniqueConstraint, Table, MetaData, select, and_,
                        insert)
from sqlalchemy.engine.base import Engine
from mautrix.types import UserID, EventID, RoomID


class TagDatabase:
    tag_groups: Table
    user_memberships: Table
    db: Engine

    def __init__(self, db: Engine, bot) -> None:
        self.db = db
        self.bot = bot
        meta = MetaData()
        meta.bind = self.db

        self.tag_groups = Table("tagbot_tag_groups", meta,
                                Column("tg_id", Integer, primary_key=True, autoincrement=True),
                                Column("group_tag", String(10), nullable=False),
                                Column("room_id", String(255), nullable=False))
        self.user_memberships = Table("tagbot_user_memberships", meta,
                                      Column("um_id", Integer, primary_key=True, autoincrement=True),
                                      Column("tag_group", Integer,
                                             ForeignKey("tagbot_tag_groups.tg_id", ondelete="CASCADE")),
                                      Column("user_id", String(255)),
                                      UniqueConstraint("tag_group", "user_id", name="tag_group_user_id_unique_idx"))
        meta.create_all()

    def _check_if_tag_exists(self, tag: str, room_id: str) -> bool:
        if self.db.execute(
                select([self.tag_groups.c.group_tag]).where(and_(self.tag_groups.c.group_tag == tag,
                                                                 self.tag_groups.c.room_id == room_id))).first() is not None:
            return True
        else:
            return False

    def _check_if_user_is_member(self, tag_id, user_id):
        if self.db.execute(
                select([self.user_memberships.c.um_id]).where(and_(
                    self.user_memberships.c.tag_group == tag_id,
                    self.user_memberships.c.user_id == user_id))).first() is not None:
            return True
        else:
            return False

    def get_all_tags(self):
        rows = self.db.execute(select([self.tag_groups.c.group_tag]))
        tags = []
        for row in rows:
            tags.append(row[0])
        return tags

    def get_members_of_group_by_tag(self, tag: str, room_id: str):
        join = self.user_memberships.join(self.tag_groups, self.user_memberships.c.tag_group == self.tag_groups.c.tg_id)
        stmt = select([self.user_memberships.c.user_id]).select_from(join).where(
            and_(self.tag_groups.c.group_tag == tag, self.tag_groups.c.room_id == room_id))
        rows = self.db.execute(stmt)
        return [row[0] for row in rows]

    def insert_new_tag(self, tag: str, room_id: str) -> bool:
        if not self._check_if_tag_exists(tag, room_id):
            self.db.execute(insert(self.tag_groups).values(group_tag=tag, room_id=room_id))
            return True
        else:
            return False

    def insert_user_membership(self, tag: str, user_id: str, room_id: str):
        res = self.db.execute(select([self.tag_groups.c.tg_id]).where(and_(self.tag_groups.c.group_tag == tag, self.tag_groups.c.room_id == room_id))).first()
        if res is not None:
            tag_id = res[0]
            if not self._check_if_user_is_member(tag_id, user_id):
                self.db.execute(insert(self.user_memberships).values(tag_group=tag_id, user_id=user_id))
                return True
            else:
                return False
