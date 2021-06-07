from sqlalchemy import (Column, String, Integer, Text, ForeignKey, Table, MetaData, select, and_, insert)
from sqlalchemy.engine.base import Engine
from mautrix.types import UserID, EventID, RoomID


class TagDatabase:
    tag_groups: Table
    user_memberships: Table
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db

        meta = MetaData()
        meta.bind = db

        self.tag_groups = Table("tagbot_tag_groups", meta,
                                Column("tg_id", Integer, primary_key=True, autoincrement=True),
                                Column("group_tag", String(10), nullable=False),
                                Column("room_id", String(255), nullable=False))
        self.user_memberships = Table("tagbot_user_memberships", meta,
                                      Column("um_id", Integer, primary_key=True, autoincrement=True),
                                      Column("tag_group", Integer, ForeignKey("tagbot_tag_groups.tg_id", ondelete="CASCADE")),
                                      Column("user_id", String(255), primary_key=True))
        meta.create_all()

    def _check_if_tag_exists(self, tag: str) -> bool:
        if len(self.db.execute(select([self.tag_groups.c.group_tag]).where(self.tag_groups.c.group_tag == tag))) > 0:
            return True
        else:
            return False

    def _check_if_user_is_member(self, tag_id, user_id):
        if len(self.db.execute(
                select([self.user_memberships.c.um_id]).where(self.user_memberships.c.user_id == user_id).and_(
                        self.user_memberships.c.tag_group == tag_id))) > 0:
            return True
        else:
            return False

    def get_all_tags(self):
        rows = self.db.execute(select([self.tag_groups.c.group_tag]))
        tags = []
        for row in rows:
            tags.append(row[0])
        return tags

    def get_members_of_group_by_tag(self, tag: str):
        join = self.user_memberships.join(self.tag_groups, self.user_memberships.c.tag_group == self.tag_groups.c.tg_id)
        stmt = select([self.user_memberships.c.user_id]).select_from(join).where(self.tag_groups.c.group_tag == tag)
        rows = self.db.execute(stmt)
        user_ids = []
        for row in rows:
            user_ids.append(row[0])
        yield user_ids

    def insert_new_tag(self, tag: str) -> bool:
        if not self._check_if_tag_exists(tag):
            self.db.execute(insert(self.tag_groups).values(group_tag=tag))
            return True
        else:
            return False

    def insert_user_membership(self, tag: str, user_id: str):
        tag_id = self.db.execute(select([self.tag_groups.c.tg_id]).where(self.tag_groups.c.group_tag == tag))
        if not self._check_if_user_is_member(tag_id, user_id):
            self.db.execute(insert(self.user_memberships).values(tag_group=tag_id, user_id=user_id))
            return True
        else:
            return False
