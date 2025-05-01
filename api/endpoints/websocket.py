# -*- coding:utf-8 -*-
"""
@Des: websocket通信模块
功能：实现带身份验证的WebSocket连接管理，支持在线用户状态同步和消息广播
"""

import json  # 取消注释：启用JSON序列化功能
import time
from fastapi import APIRouter
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket, WebSocketDisconnect
from jwt import PyJWTError
from pydantic import ValidationError
import jwt
from config import settings
from models.base import User
from schemas.base import WebsocketMessage
from typing import Any

router = APIRouter()


def check_token(token: str):
    """
    JWT令牌校验核心函数
    1. 解密token并验证签名有效性
    2. 校验用户ID有效性
    3. 异常处理包含过期、无效token等情况
    返回：验证通过返回用户ID(int)，失败返回False
    """
    try:
        # token解密
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload:
            # 用户ID
            uid = payload.get("user_id", 0)
            if uid == 0:
                return False
        else:
            return False
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
    except (PyJWTError, ValidationError):
        return False
    return uid


class Echo(WebSocketEndpoint):
    encoding = "json"
    active_connections = []  # 存储活跃连接的列表，每个连接包含用户类型、用户ID和连接对象

    async def on_connect(self, web_socket: WebSocket):
        """
        新建连接时执行
        流程：
        1. 获取连接参数和headers中的token
        2. 执行token验证和用户身份校验
        3. 清理历史连接，添加新连接
        4. 广播在线用户列表更新
        """
        u_type = web_socket.query_params.get("u_type")
        token = web_socket.headers.get("sec-websocket-protocol")
        real_ip = web_socket.headers.get('x-forwarded-for')
        real_host = web_socket.headers.get("host")

        try:

            if not u_type or not token:
                raise WebSocketDisconnect
            u_id = check_token(token)
            if not u_id:
                raise WebSocketDisconnect
            await web_socket.accept(subprotocol=token)

            for con in self.active_connections:
                # 把历史连接移除
                if con["u_id"] == u_id and con["u_type"] == u_type:
                    self.active_connections.remove(con)
            print(f"客户端ip:{real_ip} 来源:{real_host} type:{int(u_type)} ID: {int(u_id)}")
            # 加入新连接
            self.active_connections.append({
                "u_type": int(u_type),
                "u_id": int(u_id),
                "con": web_socket
            })
            online_user = await User.filter(id__in=[i['u_id'] for i in self.active_connections]).all()\
                .values("id", "username")
            data = {
                "action": 'refresh_online_user',
                "data": online_user
            }
            time.sleep(1)
            for con in self.active_connections:
                await con['con'].send_json(data)
        except WebSocketDisconnect:
            await web_socket.close()
            print("断开了连接")

    async def on_receive(self, web_socket: WebSocket, msg: Any):
        """
        接收客户端消息时触发
        功能：
        1. 校验发送者身份有效性
        2. 解析消息体并执行对应操作（当前仅支持群发）
        3. 向所有连接广播消息
        """
        try:
            token = web_socket.headers.get("Sec-Websocket-Protocol")
            user = check_token(token)
            if user:
                msg = WebsocketMessage(**msg)
                action = msg.action
                if action == 'push_msg':
                    # 群发消息
                    for i in self.active_connections:
                        msg.action = 'pull_msg'
                        msg.user = user
                        await i['con'].send_json(msg.dict())

            else:
                raise WebSocketDisconnect
        except Exception as e:
            print(e)

    async def on_disconnect(self, web_socket, close_code):
        """
        连接断开时执行
        处理流程：
        1. 从活跃连接列表中移除断开的连接
        2. 获取更新后的在线用户列表
        3. 向所有剩余连接广播更新
        """
        for con in self.active_connections:
            if con["con"] == web_socket:
                # 移除已经断开的连接
                self.active_connections.remove(con)

        online_user = await User.filter(id__in=[i['u_id'] for i in self.active_connections]).all() \
            .values("id", "username", "header_img")
        data = {
            "action": 'refresh_online_user',
            "data": online_user
        }
        for con in self.active_connections:
            await con['con'].send_json(data)

    async def send_message(self,
                           web_socket: WebSocket,
                           sender: int,
                           sender_type: int,
                           recipient: int,
                           recipient_type: int,
                           data: dict):
        """
        消息发送
        :param web_socket: 发送者连接对象
        :param sender: 发送者ID
        :param sender_type: 发送者用户类型
        :param recipient: 接收者用户ID
        :param recipient_type: 接收者用户类型
        :param data: 要发送的数据
        :return:
        """
        is_online = False  # 用户在线状态
        for con in self.active_connections:
            # 找到到对方
            if con["u_id"] == recipient and con["u_type"] == recipient_type:
                is_online = True
                message = {
                    "sender": sender,
                    "sender_type": sender_type,
                    "data": data
                }
                print(data)
                await con["con"].send_text(json.dumps(message))
        # 用户是否在线
        if is_online:
            await web_socket.send_text('{"send_status":"send-success"}')
        else:
            await web_socket.send_text('{"send_status":"send-fail"}')


router.add_websocket_route('/test', Echo)
