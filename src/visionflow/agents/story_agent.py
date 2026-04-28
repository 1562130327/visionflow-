"""故事创作 Agent — 主题理解 → 剧本生成 → 分镜拆解"""

import json
import re
from openai import OpenAI
from loguru import logger
from datetime import datetime
from typing import Optional

from visionflow.config import get_settings

settings = get_settings()


class StoryProject:
    """一个完整的创作项目"""

    def __init__(self, theme: str):
        self.id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.title = ""
        self.theme = theme
        self.genres: list[str] = []
        self.style: str = ""
        self.characters: list[dict] = []
        self.plot: str = ""
        self.scenes: list[Scene] = []
        self.created_at = datetime.now().isoformat()


class Scene:
    """单个分镜"""

    def __init__(self, index: int, desc: str, dialogue: str, mood: str, camera: str, prompt: str, negative: str = ""):
        self.index = index
        self.desc = desc
        self.dialogue = dialogue
        self.mood = mood
        self.camera = camera
        self.prompt = prompt
        self.negative = negative
        self.image_url: Optional[str] = None
        self.video_url: Optional[str] = None
        self.audio_url: Optional[str] = None

    def to_dict(self):
        return {
            "index": self.index,
            "desc": self.desc,
            "dialogue": self.dialogue,
            "mood": self.mood,
            "camera": self.camera,
            "prompt": self.prompt,
            "negative": self.negative,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "audio_url": self.audio_url,
        }


class StoryAgent:
    """对话式故事创作 Agent"""

    def __init__(self):
        # 先用 DeepSeek 作为 LLM（稳定可靠）
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self.model = settings.deepseek_model
        self._current_project: Optional[StoryProject] = None

    @property
    def current_project(self) -> Optional[StoryProject]:
        return self._current_project

    # ─── Step 1: 理解主题 ───

    def understand_theme(self, user_input: str) -> dict:
        """理解用户输入的主题并生成结构化大纲"""
        sys_prompt = """你是一位专业的 AI 漫剧导演。用户给你一个创作想法，你需要：
1. 提炼主题名称（简洁有力）
2. 判断风格类型（古风/仙侠/现代/校园/悬疑/科幻/热血/恋爱等）
3. 给出故事基调（史诗/轻松/黑暗/治愈等）
4. 设计2-4个核心角色（名称、性格一句话、外形要点）
5. 写出故事大纲（起承转合，100-200字）

以 JSON 格式输出，不要加 markdown 标记：
{
  "title": "主题名",
  "genres": ["类型1", "类型2"],
  "style": "画风基调描述",
  "characters": [
    {"name": "角色名", "personality": "性格", "appearance": "外形"}
  ],
  "plot": "故事大纲"
}"""

        resp = self._call_llm(system=sys_prompt, user=user_input)
        data = self._parse_json(resp)
        logger.info(f"[StoryAgent] 主题理解完成: {data.get('title', '?')}")
        return data

    # ─── Step 2: 生成分镜 ───

    def generate_scenes(self, theme_data: dict, count: int = 6) -> list[Scene]:
        """根据主题生成分镜列表"""
        sys_prompt = f"""你是一位电影分镜师。根据以下主题生成 {count} 个分镜。
每个分镜包含：
- desc: 画面描述（50-80字，具体到角色动作、环境细节）
- dialogue: 旁白/对白文本（如果是配音台词）
- mood: 氛围（如「悲壮」「温馨」「紧张」）
- camera: 镜头语言（如「远景俯拍」「面部特写」「缓慢推近」）
- prompt: AI 绘图提示词（英文，具体描述角色、动作、场景、光影、构图）。
  如果是魔幻国漫画风，prompt 开头加上"Dark fantasy Chinese mythology, epic style, mystical atmosphere,"
- negative: 负面提示词（英文）

以 JSON 数组格式输出：
[
  {{
    "index": 1,
    "desc": "描述文字",
    "dialogue": "台词",
    "mood": "氛围",
    "camera": "镜头",
    "prompt": "英文提示词",
    "negative": "nsfw, deformed, bad anatomy, blurry"
  }}
]

主题信息：
- 标题：{theme_data.get('title', '')}
- 类型：{', '.join(theme_data.get('genres', []))}
- 画风：{theme_data.get('style', '')}
- 角色：{json.dumps(theme_data.get('characters', []), ensure_ascii=False)}
- 大纲：{theme_data.get('plot', '')}
"""

        resp = self._call_llm(system=sys_prompt, user="请生成分镜")
        scenes = self._parse_json(resp)
        if not isinstance(scenes, list):
            if isinstance(scenes, dict):
                scenes = scenes.get("scenes", scenes.get("fentou", []))
        result = []
        for s in scenes:
            result.append(Scene(
                index=s.get("index", len(result) + 1),
                desc=s.get("desc", ""),
                dialogue=s.get("dialogue", ""),
                mood=s.get("mood", ""),
                camera=s.get("camera", ""),
                prompt=s.get("prompt", ""),
                negative=s.get("negative", "nsfw, deformed, bad anatomy, blurry, low quality"),
            ))
        logger.info(f"[StoryAgent] 生成了 {len(result)} 个分镜")
        return result

    # ─── 内部方法 ───

    def _call_llm(self, system: str, user: str) -> str:
        """调用小米 LLM"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.8,
                max_tokens=4096,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"[StoryAgent] LLM 调用失败: {e}")
            raise

    def _parse_json(self, text: str) -> dict | list:
        """从 LLM 回复中提取 JSON"""
        # 尝试找 {} 或 [] 包裹的内容
        text = text.strip()
        # 去掉 ```json 和 ``` 标记
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找第一个 { 或 [
            for delim in ('{', '['):
                start = text.find(delim)
                if start >= 0:
                    end = text.rfind('}' if delim == '{' else ']')
                    if end > start:
                        try:
                            return json.loads(text[start:end+1])
                        except json.JSONDecodeError:
                            pass
            logger.error(f"[StoryAgent] JSON 解析失败:\n{text[:300]}")
            return {"error": "parse_failed", "raw": text[:500]}
