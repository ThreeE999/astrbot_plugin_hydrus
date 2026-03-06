import asyncio
import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.core.message.components import Image
from astrbot.core.config import AstrBotConfig
import hydrus_api


def handle_tags_alias(tags_alias: list) -> dict[str, list]:
    r: dict[str, list] = {}
    for alias in tags_alias:
        tags = alias.get("tags", [])
        if alias.get("__template_key") == "exclusive":
            continue
        if len(tags) <= 1 or alias.get("__template_key") == "AND":
            r[alias.get("alias_name")] = tags
        elif alias.get("__template_key") == "OR":
            r[alias.get("alias_name")] = [tags]
    return r


def handle_exclusive_tags(tags_alias: list) -> dict[str, list]:
    r: dict[str, list] = {}
    for alias in tags_alias:
        tags = alias.get("tags", [])
        if alias.get("__template_key") == "exclusive":
            for tag in tags:
                r[tag] = tags
    return r


def expand_tags_recursive(
    items: list,
    tags_alias: dict[str, list],
    seen: set[str] | None = None,
) -> list:
    """递归展开别名。AND 展平；OR 保持为 list 一项不展平。别名可嵌套，seen 防环。"""
    if seen is None:
        seen = set()
    result: list = []
    for item in items:
        if isinstance(item, list):
            # OR 结构：保留为 list，只递归展开其内容
            result.append(expand_tags_recursive(item, tags_alias, seen))
        elif isinstance(item, str):
            if item in tags_alias and item not in seen:
                seen.add(item)
                try:
                    value = tags_alias[item]
                    # OR 类型：value 为 [tags]，保留一层 list
                    if len(value) == 1 and isinstance(value[0], list):
                        result.append(expand_tags_recursive(value[0], tags_alias, seen))
                    else:
                        result.extend(expand_tags_recursive(value, tags_alias, seen))
                finally:
                    seen.discard(item)
            else:
                result.append(item)
        else:
            result.append(str(item))
    return result


class HydrusAPI(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.tags_alias = handle_tags_alias(self.config.tags_alias)
        self.exclusive_tags = handle_exclusive_tags(self.config.tags_alias)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.client = hydrus_api.Client(self.config.api_key, self.config.hydrus_host)

    @filter.command("hydrus")
    async def hydrus(self, event: AstrMessageEvent):
        """调取hydrus的API，返回图片。"""
        tags = event.get_message_str().split()[1:]
        # 用 dict 保持插入顺序，O(1) 查找与删除，最后按顺序得到列表
        search_tags_pre: dict[str, None] = {}
        for tag in self.config.force_tags + tags:
            tag = tag.strip().lower()
            if not tag:
                continue
            to_remove = {
                tag,
                tag[1:] if tag.startswith("-") else "-" + tag,
                *self.exclusive_tags.get(tag, []),
            }
            for _tag in to_remove:
                search_tags_pre.pop(_tag, None)
            search_tags_pre[tag] = None

        search_tags = expand_tags_recursive(list(search_tags_pre), self.tags_alias)
        logger.debug(f"search tags: {search_tags}")
        file_content = await self.get_random_image(search_tags)
        if file_content is not None:
            yield event.chain_result([Image.fromBytes(file_content)])
        else:
            yield event.plain_result("没有找到图片")

    async def get_random_image(self, search_tags: list[str]):
        try:
            file_sort_type = 2
            # hydrus_api 是同步库，用 to_thread 避免阻塞事件循环
            # https://hydrusnetwork.github.io/hydrus/developer_api.html#get_files_search_files
            file_ids = (
                await asyncio.to_thread(
                    self.client.search_files, search_tags, file_sort_type=file_sort_type
                )
            )["file_ids"]
            total_files = len(file_ids)
            if total_files == 0:
                return
            random_file_id = random.choice(file_ids)
            file_response = await asyncio.to_thread(
                self.client.get_file, file_id=random_file_id
            )
            file_content = file_response.content
            return file_content
        except Exception as e:
            logger.error(f"search files failed: {str(e)}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        self.client = None
