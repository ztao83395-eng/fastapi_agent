from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRequest(BaseModel):
    username: str
    password: str



class UserInfoBase(BaseModel):
    """
    ⽤户信息基础数据模型
    """
    nickname:Optional[str]=Field(None,max_length=50,description="昵称"
    )
    avatar:Optional[str]=Field(None,max_length=255,description="头像URL")
    gender:Optional[str]=Field(None,max_length=10,description="性别")
    bio:Optional[str]=Field(None,max_length=500,description="个⼈简介")

#user_info 对应的类：基础类 +Info类（id,用户名）
class UserInfoResponse(UserInfoBase):
    """用户完整信息响应：含全部资料字段，
    否则前端保存昵称后拿不到新值（只有 id/username 会导致"改昵称不生效"）"""
    id:int
    username:str
    phone:Optional[str]=Field(None,max_length=20,description="手机号")
    #模型类配置
    model_config=ConfigDict(
        from_attributes=True,
    )

#data数据类型
class UserAuthResponse(BaseModel):
    token:str
    user_info: UserInfoResponse = Field(..., alias="userInfo")

    #模型类配置
    model_config=ConfigDict(
        populate_by_name=True,  #alias/字段名兼容
        from_attributes=True,   #允许从ORM对象属性中取值
    )


#更新用户信息的模型类
class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    gender: str | None = None
    bio: str | None = None  # 个人简介
    phone: str | None = None



#修改密码
class UserUpdatePassword(BaseModel):
    old_password: str=Field(...,alias="oldPassword",description="旧密码")
    new_password: str=Field(...,min_length=6,alias="newPassword",description="新密码")


#忘记密码重置（不验证身份，演示项目最简方案）
class UserResetPassword(BaseModel):
    username: str=Field(...,description="用户名")
    new_password: str=Field(...,min_length=6,alias="newPassword",description="新密码")

