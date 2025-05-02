# -*- coding:utf-8 -*-
"""
"""
from api.api import api_router
from views.views import views_router
from fastapi import APIRouter


router = APIRouter()
# 视图路由 将分支路由聚合起来
router.include_router(views_router)
# API路由
router.include_router(api_router)

