# -*- coding:utf-8 -*-
"""
@Time : 2022/5/15 11:51 PM
@Author: binkuolo
@Des: 角色管理接口模块
提供角色的CRUD操作，包含权限控制和数据验证
"""
from typing import List
from fastapi import Query, APIRouter, Security
from core.Auth import check_permissions
from core.Response import res_antd, success, fail
from schemas.role import CreateRole, UpdateRole, RoleList
from models.base import Role
from tortoise.queryset import F
router = APIRouter(prefix='/role')


@router.get("/all", summary="所有角色下拉选项专用")
async def all_roles_options(user_id: int = Query(None)):
    """
    获取启用状态的角色列表用于前端下拉选择
    特殊功能：当传入user_id时返回该用户已关联的角色ID列表
    
    参数说明：
        user_id (int, optional): 需要查询关联角色的用户ID，默认不传
    
    响应结构：
        {
            "all_role": [{"label": roleName, "value": roleId}],  // 所有启用角色
            "user_roles": [roleId1, roleId2]  // 用户关联角色ID列表
        }
    """
    # 查询启用的角色
    roles = await Role.annotate(label=F("role_name"), value=F('id')).filter(role_status=True).values('label', "value")
    user_roles = []
    if user_id:
        # 当前用户角色
        user_role = await Role.filter(user__id=user_id, role_status=True).values_list('id')
        user_roles = [i[0] for i in user_role]
    data = {
        "all_role": roles,
        "user_roles": user_roles
    }
    return success(msg="所有角色下拉选项专用", data=data)


@router.post("", summary="角色添加")
async def create_role(post: CreateRole):
    """
    创建新角色接口
    权限要求：role_add
    
    请求体参数：
        post (CreateRole): 包含角色名称、描述等必要字段的创建对象
    
    返回示例：
        成功: {"code": 200, "msg": "创建成功!"}
        失败: {"code": 400, "msg": "创建失败!"}
    """
    result = await Role.create(**post.dict())
    if not result:
        return fail(msg="创建失败!")
    return success(msg="创建成功!")


@router.delete("", summary="角色删除")
async def delete_role(role_id: int):
    """
    删除指定角色接口
    权限要求：role_delete
    
    参数说明：
        role_id (int): 待删除角色的数据库主键ID
    
    返回示例：
        成功: {"code": 200, "msg": "删除成功!"}
        失败: {"code": 400, "msg": "角色不存在/删除失败!"}
    """
    role = await Role.get_or_none(pk=role_id)
    if not role:
        return fail(msg="角色不存在!")
    result = await Role.filter(pk=role_id).delete()
    if not result:
        return fail(msg="删除失败!")
    return success(msg="删除成功!")


@router.put("", summary="角色修改")
async def update_role(post: UpdateRole):
    """
    更新角色基础信息接口
    权限要求：role_update
    
    请求体参数：
        post (UpdateRole): 包含id及其他可更新字段的对象
    
    返回示例：
        成功: {"code": 200, "msg": "更新成功!"}
        失败: {"code": 400, "msg": "更新失败!"}
    """
    data = post.dict()
    data.pop("id")
    result = await Role.filter(pk=post.id).update(**data)
    if not result:
        return fail(msg="更新失败!")
    return success(msg="更新成功!")


@router.get('', summary="角色列表")
async def get_all_role(
        pageSize: int = 10,
        current: int = 1,
        role_name: str = Query(None),
        role_status: bool = Query(None),
        create_time: List[str] = Query(None)
) -> RoleList:
    """
    分页查询角色列表接口
    权限要求：role_query
    
    支持过滤条件：
        pageSize: 每页记录数
        current: 当前页码
        role_name: 按名称模糊查询
        role_status: 按启用状态过滤
        create_time: 按创建时间范围过滤
    
    返回格式：
        Ant Design Pro Table标准分页格式:
        {
            "data": [...],
            "total": 总记录数,
            "success": True
        }
    """
    query = {}
    if role_name:
        query.setdefault('role_name', role_name)
    if role_status is not None:
        query.setdefault('role_status', role_status)
    if create_time:
        query.setdefault('create_time__range', create_time)

    role = Role.annotate(key=F("id")).filter(**query).all()
    # 总数
    total = await role.count()
    # 查询
    data = await role.limit(pageSize).offset(pageSize * (current - 1)).order_by("-create_time") \
        .values(
        "key", "id", "role_name", "role_status", "role_desc", "create_time", "update_time")
    return res_antd(code=True, data=data, total=total)
