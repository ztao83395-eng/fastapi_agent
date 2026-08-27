import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_database
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserUpdatePassword, UserResetPassword
from crud import users, favorite
from utils.auth import get_current_user
from utils.response import success_response

router=APIRouter(prefix="/api/users",tags=["users"])

# 头像保存目录：static/avatars/（main.py 已把 /static 挂载为静态资源，图片可直接访问）
AVATAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "avatars")
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


@router.post("/register")
async def register(user_data:UserRequest,db:AsyncSession=Depends(get_database)):
    #注册逻辑:验证用户是否存在->创建用户->生成Token ->响应结果
    existing_user=await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="用户已存在")
    user=await users.create_user(db, user_data)
    token=await users.create_token(db, user.id)
    # return {
    #     "code": 200,
    #     "message": "注册成功",
    #     "data": {
    #         "token": token,
    #         "userInfo": {
    #             "id": user.id,
    #             "username": user.username,
    #             "bio": user.bio,
    #             "avatar":user.avatar,
    #         }
    #     }
    # }
    response_data=UserAuthResponse(token=token,user_info=UserInfoResponse.model_validate(user))
    return success_response(message="success",data=response_data)


#用户登录
@router.post("/login")
async def login(user_data:UserRequest,db:AsyncSession=Depends(get_database)):
    #登录逻辑：验证用户是否存在->验证密码 -> 生成Token ->响应结果
    user=await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户或密码错误")
    token=await users.create_token(db, user.id)
    response_data=UserAuthResponse(token=token,user_info=UserInfoResponse.model_validate(user))

    print("response_data 原始对象:", response_data)
    print("response_data.model_dump():", response_data.model_dump())
    print("response_data.model_dump(by_alias=True):", response_data.model_dump(by_alias=True))

    return success_response(message="登陆成功啦", data=response_data)



#获取用户信息
#查Token查用户-》封装crud -》功能整合成一个工具函数 -》路由导入使用
@router.get("/info")
async def get_user_info(user:User = Depends(get_current_user)):
    return success_response(message="success",data=UserInfoResponse.model_validate(user))


#修改用户信息
#修改用户信息：验证Token -> 更新（用户输入数据 put提交 -》请求体参数 -》定义Pydantic类）-》响应结果
@router.put("/update")
async def update_user_info(
        user_data:UserUpdateRequest,
        user:User = Depends(get_current_user),
        db:AsyncSession=Depends(get_database),
):
    updated_user=await users.update_user(db,user.username,user_data)
    return success_response(message="更新用户信息成功",data=UserInfoResponse.model_validate(updated_user))

#上传头像（需登录）：保存到 static/avatars/，返回可访问的 URL
@router.post("/avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        user: User = Depends(get_current_user),
):
    # 校验图片类型（按扩展名白名单）
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp 格式的图片")

    # 校验大小（读入内存判断）
    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过 2MB")

    # 随机文件名（uuid 十六进制），避免重名覆盖
    os.makedirs(AVATAR_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/static/avatars/{filename}"
    return success_response(message="上传成功", data={"url": url})

#忘记密码重置（无需登录、不验证身份）：用户名存在 -》 直接改新密码
@router.post("/reset-password")
async def reset_password(user_data:UserResetPassword,db:AsyncSession=Depends(get_database)):
    res=await users.reset_password(db,user_data.username,user_data.new_password)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="用户不存在")
    return success_response(message="重置密码成功")


#修改密码
@router.put("/password")
async def update_password(
        password_data:UserUpdatePassword,
        user:User = Depends(get_current_user),
        db:AsyncSession=Depends(get_database),
):
    res_change_pwd=await users.update_password(db,user,password_data.old_password,password_data.new_password)
    if not res_change_pwd:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="修改密码失败")
    return success_response(message="修改密码成功")

