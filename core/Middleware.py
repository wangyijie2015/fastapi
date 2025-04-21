# -*- coding:utf-8 -*-
"""
@Des: 中间件  Web 应用的性能监控、会话管理和请求追踪等场景。
"""

import time
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from fastapi import Request
from core.Utils import random_str


class BaseMiddleware:
    """
    Middleware
    """

    def __init__(
            self,
            app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # 非http协议  拿出HTTP请求
            await self.app(scope, receive, send)
            return
        # 记录开始事件
        start_time = time.time()
        # 创建 Request 对象并处理 session：
        req = Request(scope, receive, send)
        if not req.session.get("session"):
            req.session.setdefault("session", random_str())

        # 定义 send_wrapper 函数：这是一个包装函数，用于拦截响应消息
        # 计算请求处理时间
        # 如果是响应开始消息，添加 X-Process-Time 头
        async def send_wrapper(message: Message) -> None:
            process_time = time.time() - start_time
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Process-Time", str(process_time))
            await send(message)
        # 调用下层应用：将包装后的 send 函数传递给下层应用
        await self.app(scope, receive, send_wrapper)
