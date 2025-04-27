# -*- coding:utf-8 -*-

from pydantic import BaseModel, Field
from typing import List, Any, Optional


# 标准的api响应格式，适用于Json数据的接口
# code (int): HTTP 状态码（如 200 表示成功，400 表示客户端错误）。
# message (str): 返回的提示信息（如 "操作成功" 或 "参数错误"）。
# data (List): 返回的具体数据（通常是列表形式，但可以进一步用泛型优化）。
class BaseResp(BaseModel):
    code: int = Field(description="状态码")
    message: str = Field(description="信息")
    data: List = Field(description="数据")

# 专为前端分页表格（如 Ant Design Table）设计的响应格式。
# success (bool): 请求是否成功（True/False）。
# data (List): 当前页的数据列表。
# total (int): 数据总条数（用于分页计算）。
class ResAntTable(BaseModel):

    success: bool = Field(description="状态码")
    data: List = Field(description="数据")
    total: int = Field(description="总条数")


# 作用：定义 WebSocket 通信的消息结构。
# 字段：
# action (Optional[str]): 消息类型（如 "join"、"message"）。
# user (Optional[int]): 用户 ID（标识消息来源或目标）。
# data (Optional[Any]): 任意类型的消息内容（如字符串、JSON 对象等）

# WebsocketMessage 支持 WebSocket 消息的标准化解析。
class WebsocketMessage(BaseModel):
    action: Optional[str]
    user: Optional[int]
    data: Optional[Any]


class WechatOAuthData(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    unionid: Optional[str]
    scope: str
    openid: str

# 作用：解析微信 OAuth2.0 授权后返回的数据（如通过 code 换取 access_token）。
# 字段：
# access_token (str): 接口调用凭证。
# expires_in (int): 过期时间（秒）
# refresh_token (str): 刷新 access_token 的令牌。
# unionid (Optional[str]): 用户统一标识（跨公众号/小程序时可用）。
# scope (str): 授权作用域（如 snsapi_userinfo）。
# openid (str): 用户在当前公众号/小程序的唯一标识。
class WechatUserInfo(BaseModel):
    openid: str
    nickname: str
    sex: int
    city: str
    province: str
    country: str
    headimgurl: str
    unionid: Optional[str]
