# Bangumi 同步工具

这是一个用于在不同动画数据库平台之间同步观看记录的工具。目前支持从 Bangumi 同步到 MyAnimeList (MAL) 和 AniList。

## 功能特点

- 从 Bangumi 获取观看记录
- 通过 DandanPlay API 进行动画匹配
- 支持同步到 MyAnimeList (MAL)
- 可选同步到 AniList
- 支持缓存匹配结果，提高后续同步速度
- 自动处理评分和观看状态的转换

## 安装要求

- Python 3.8+
- 需要的第三方库：
  ```bash
  pip install requests
  ```

## 配置说明

在 `bangumi.py` 中的 `CONFIG` 字典可以修改以下配置：

- `username`: Bangumi 用户名
- `mal_username`: MyAnimeList 用户名
- `anilist_username`: AniList 用户名
- `dandanplay_api_key`: DandanPlay API 密钥
- `cache_file`: 缓存文件路径

## 使用方法

1. 首先配置你的 Bangumi token 和用户名
[BGM API](https://next.bgm.tv/demo/access-token)

2. 运行程序：
   ```bash
   python bangumi.py
   ```

3. 按照提示完成认证流程：
   - 程序会自动打开浏览器进行 MAL 认证
   - 如果启用了 AniList，还需要进行 AniList 认证
   - 复制认证页面显示的 access token 并粘贴到程序中

4. 等待同步完成

## 注意事项

- 首次运行时会创建新的匹配缓存
- 后续运行会使用缓存的匹配结果，加快同步速度
- 如需强制更新匹配结果，可以删除 `anime_mappings.json` 文件
- 建议不要频繁同步，注意遵守各平台的 API 使用限制

## 常见问题

1. **认证失败**
   - 检查网络连接
   - 确保复制的 token 完整且正确

2. **同步失败**
   - 检查 Bangumi token 是否有效
   - 确认用户名是否正确
   - 查看日志文件了解详细错误信息
   - 注意：由于DDPlay需要url签名，所以需要连接到自建服务器（默认位于OVH法国），有能力可以自己申请弹弹开放平台搭建

## 许可证

MIT License
