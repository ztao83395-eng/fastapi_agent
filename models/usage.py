from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class AiUsage(Base):
    """AI 调用 token 用量记录（用于每日额度限制与消费统计）"""

    __tablename__ = "ai_usage"

    __table_args__ = (
        Index('idx_usage_user_time', 'user_id', 'created_at'),  # 按用户+时间统计用量
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True, comment="记录ID")
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('user.id'), nullable=False, comment="用户ID")
    prompt_tokens: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False, comment="输入token数")
    completion_tokens: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False, comment="输出token数")
    total_tokens: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False, comment="总token数")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<AiUsage(id={self.id}, user_id={self.user_id}, total={self.total_tokens})>"
