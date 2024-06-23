# bgm_to_mal
## 一个轻松将追番记录从Bangumi搬运Mal的脚本
### **注意：依赖requests**

## 提前准备：
### 1.bgm api token [API网站](https://next.bgm.tv/demo/access-token)
### 2.mal api
## 如何创建mal api:
### 1.打开你的mal个人资料 寻找api选项 
### 2.CreateID [网站](https://myanimelist.net/apiconfig/create)
### 3.APP Type选web 
### App Redirect URL填http://127.0.0.1
### 其他随便填 创建完后记录下CLIENT_ID和CLIENT_SECRET

## 如何使用
### 1.直接下载本项目源码
### 2.确保你电脑中的python环境已经安装requests库
### * 修改mal_auth.py下的CLIENT_ID和CLIENT_SECRET
### 3.执行apis目录下的mal_auth.py文件鉴权
### 控制台会输出一段网站 访问 登陆后将跳转到的网站后面的code=后面的token复制到控制台
### 4.修改bangumi.py 将bangumi_token和bangumi_user(用户名或bgm id)改成你自己的
### 5.运行bangumi.py

## 对于Anilist:
### 你需要申请anl的CLIENT_ID和CLIENT_SECRET填写到anl_auth.py中
### 然后运行anl_auth.py 并在bangumi.py中取消注释最下面和anl有关的几行代码