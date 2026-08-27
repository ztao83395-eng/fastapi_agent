from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from models import Base
from .users import User


class ChatSession(Base):
    """AI 对话会话（ChatGPT 式多会话，一个用户可有多个会话）"""

    __tablename__ = "chat_session"

    __table_args__ = (
        Index('idx_session_user', 'user_id', 'updated_at'),  # 按用户列会话，按更新时间倒序
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True, comment="会话ID")
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey(User.id), nullable=False, comment="用户ID")
    title: Mapped[str] = mapped_column(String(100), default="新对话", nullable=False, comment="会话标题")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后消息时间")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title={self.title})>"


class ChatMessage(Base):
    """AI 对话消息（一条用户提问或一条助手回答）"""

    __tablename__ = "chat_message"

    __table_args__ = (
        Index('idx_msg_session', 'session_id', 'id'),  # 按会话取消息，按 id 正序
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True, comment="消息ID")
    session_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('chat_session.id', ondelete='CASCADE'), nullable=False, comment="所属会话ID")
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="角色：user/assistant")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session={self.session_id}, role={self.role})>"
