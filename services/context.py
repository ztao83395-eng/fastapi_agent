#线程安全的上下文变量，用于在异步或并发环境中传递当前用户ID。

from contextvars import ContextVar

current_user_id_var: ContextVar[int] = ContextVar("current_user_id", default=0)

def get_current_user_id() -> int:
    return current_user_id_var.get()
