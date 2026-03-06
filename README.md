# astrbot-plugin-hydrus

AstrBot 插件：通过 tag 调用 [Hydrus network](https://hydrusnetwork.github.io/hydrus/) API，搜索并返回随机图片。

## 功能

- **命令**：`hydrus <tag1> <tag2> ...` — 按 tag 在 Hydrus 中搜索，随机返回一张图片
- **Tag 别名**：支持 AND（且）、OR（或）、Exclusive（互斥）三种关系，可嵌套
- **强制 tag**：可配置默认参与搜索的 tag（如 `system:archive`、`system:filetype = image/jpg, image/png`、`-r18` 等）

## 配置

在 AstrBot 中配置本插件时需填写：

| 配置项 | 说明 |
|--------|------|
| **hydrus_host** | Hydrus API 地址，如 `http://127.0.0.1:45869` |
| **api_key** | Hydrus API Key，需在 Hydrus 客户端中生成并具备相应权限 |
| **force_tags** | 每次搜索都会带上的 tag 列表，默认示例：`system:archive`、`system:filetype = image/jpg, image/png`、`-r18` |
| **tags_alias** | Tag 别名与互斥：**AND**（且关系组合）、**OR**（或关系组合）、**Exclusive**（互斥关系，同组内不能同时出现，保留最后一个），所有别名支持嵌套。|

Tag 搜索与系统 tag 说明见 [Hydrus 官方 API 文档](https://hydrusnetwork.github.io/hydrus/developer_api.html#get_files_search_files)。

## 使用示例

- `hydrus cat` — 搜索带 `cat` 的图片
- `hydrus cat dog` — 搜索同时带 `cat` 和 `dog` 的图片
- `hydrus -dog` — 排除 `dog`（与 `dog` 互斥，保留最后一个）
- 若配置了别名，可直接使用别名参与搜索

## 功能规划

- [√] 按tag实现随机图片调用。
- [×] 支持视频文件。
- [×] 将用户发送的图片上传到hydrus。
- [×] 修改图片tag或其他数据。
- [×] archive/inbox等转换。
- [×] llm tool调用。
- [×] ......
