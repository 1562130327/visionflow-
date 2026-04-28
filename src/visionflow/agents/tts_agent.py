"""语音合成 Agent — 调用小米 Mimo TTS API"""

import base64
import os
from openai import OpenAI
from loguru import logger
from visionflow.config import get_settings

settings = get_settings()


class TTSAgent:
    """小米 Mimo TTS 语音合成"""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.mimo_api_key,
            base_url=settings.mimo_base_url,
        )

    def synthesize(self, text: str, mood: str = "平静", voice: str = "冰糖") -> bytes:
        """将文本合成为语音，返回 wav 字节"""
        # 用自然语言控制风格
        mood_prompt = self._mood_to_prompt(mood)
        try:
            resp = self.client.chat.completions.create(
                model="MiMo-V2.5-TTS",
                messages=[
                    {"role": "user", "content": mood_prompt},
                    {"role": "assistant", "content": text},
                ],
                audio={"format": "wav", "voice": voice},
            )
            message = resp.choices[0].message
            audio_bytes = base64.b64decode(message.audio.data)
            logger.info(f"[TTS] 合成成功: {len(text)} 字, {len(audio_bytes)} 字节")
            return audio_bytes
        except Exception as e:
            logger.error(f"[TTS] 合成失败: {e}")
            raise

    def _mood_to_prompt(self, mood: str) -> str:
        """将中文氛围描述转为 TTS 指令"""
        mapping = {
            "悲壮": "低沉缓慢，带着苍凉的悲剧感，语气坚定但隐含着悲伤",
            "紧张": "语速稍快，带着压抑的焦虑感，声音略紧绷",
            "温馨": "温柔轻缓，带着暖意，像在轻声诉说",
            "恐惧": "颤抖的声音，语速急促，呼吸声明显，充满害怕",
            "愤怒": "声音低沉有力，咬字重，带着压抑的怒火",
            "神秘": "语速缓慢，带着低沉的磁性，像在讲述古老的秘密",
            "欣喜": "语调上扬，轻快活泼，带着藏不住的喜悦",
            "史诗": "庄严宏大，语调沉稳，每个字都掷地有声",
        }
        return mapping.get(mood, "用自然平和的语调朗读，语速适中")
