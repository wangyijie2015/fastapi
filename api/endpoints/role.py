# -*- coding:utf-8 -*-
"""
@Time : 2022/5/15 11:51 PM
@Author: binkuolo
@Des: 角色管理
"""
from typing import List
from fastapi import Query, APIRouter, Security
from core.Auth import check_permissions
from core.Response import res_antd, success, fail
from schemas.role import CreateRole, UpdateRole, RoleList
from models.base import Role
from tortoise.queryset import F
router = APIRouter(prefix='/role')


@router.get("/all", summary="所有角色下拉选项专用", dependencies=[Security(check_permissions, scopes=["user_role"])])
async def all_roles_options(user_id: int = Query(None)):
    """
    获取所有启用状态的角色选项（用于前端下拉菜单）
    若传入用户ID，同时返回该用户已关联的角色ID列表
    
    参数:
        user_id (int, optional): 用户ID用于查询其关联角色
        
    返回:
        {
            "all_role": [{"label": roleName, "value": roleId}], 
            "user_roles": [roleId1, roleId2]
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


@router.post("", summary="角色添加", dependencies=[Security(check_permissions, scopes=["role_add"])])
async def create_role(post: CreateRole):
    """
    创建新角色接口
    需要role_add权限
    
    参数:
        post (CreateRole): 包含角色名称、描述等必要字段的创建对象
        
    返回:
        成功: {"code": 200, "msg": "创建成功!"}
        失败: {"code": 400, "msg": "创建失败!"}
    """
    result = await Role.create(**post.dict())
    if not result:
        return fail(msg="创建失败!")
    return success(msg="创建成功!")


@router.delete("", summary="角色删除", dependencies=[Security(check_permissions, scopes=["role_delete"])])
async def delete_role(role_id: int):
    """
    删除指定ID的角色
    需要role_delete权限
    
    参数:
        role_id (int): 待删除角色的数据库主键ID
        
    返回:
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


@router.put("", summary="角色修改", dependencies=[Security(check_permissions, scopes=["role_update"])])
async def update_role(post: UpdateRole):
    """
    更新角色基础信息
    需要role_update权限
    
    参数:
        post (UpdateRole): 包含id及其他可更新字段的对象
        
    返回:
        成功: {"code": 200, "msg": "更新成功!"}
        失败: {"code": 400, "msg": "更新失败!"}
    """
    data = post.dict()
    data.pop("id")
    result = await Role.filter(pk=post.id).update(**data)
    if not result:
        return fail(msg="更新失败!")
    return success(msg="更新成功!")


@router.get('', summary="角色列表", response_model=RoleList,
            dependencies=[Security(check_permissions, scopes=["role_query"])])
async def get_all_role(
        pageSize: int = 10,
        current: int = 1,
        role_name: str = Query(None),
        role_status: bool = Query(None),
        create_time: List[str] = Query(None)
) -> RoleList:
    """
    分页查询角色列表
    需要role_query权限
    
    参数:
        pageSize (int): 每页记录数
        current (int): 当前页码
        role_name (str, optional): 按角色名称模糊查询
        role_status (bool, optional): 按启用状态过滤
        create_time (List[str], optional): 按创建时间范围过滤
        
    返回:
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
