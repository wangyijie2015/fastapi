# -*- coding:utf-8 -*-

from core.Auth import create_access_token  # 导入用于生成JWT令牌的函数
from fastapi.security.oauth2 import OAuth2PasswordRequestForm  # 导入OAuth2表单模型
from fastapi import Depends, HTTPException  # 导入FastAPI依赖注入和HTTP异常处理


async def test_oath2(data: OAuth2PasswordRequestForm = Depends()):
    """
    测试OAuth2认证的端点函数
    
    参数:
        data (OAuth2PasswordRequestForm): OAuth2认证表单数据，包含用户名、密码和作用域
    
    返回:
        dict: 包含访问令牌和令牌类型的字典
    """
    user_type = False  # 初始化用户类型为False，表示普通用户
    
    # 检查是否有指定的作用域
    if not data.scopes:
        raise HTTPException(401, "请选择作用域!")  # 如果没有作用域，抛出401未授权异常
    
    # 检查作用域中是否包含"is_admin"
    if "is_admin" in data.scopes:
        user_type = True  # 如果包含"is_admin"，将用户类型设置为True，表示管理员
    
    # 准备JWT令牌的数据
    jwt_data = {
        "user_id": data.client_id,  # 用户ID，从表单的client_id字段获取
        "user_type": user_type  # 用户类型，True表示管理员，False表示普通用户
    }
    
    # 调用create_access_token函数生成JWT令牌
    jwt_token = create_access_token(data=jwt_data)
    
    # 返回包含访问令牌和令牌类型的字典
    return {"access_token": jwt_token, "token_type": "bearer"}