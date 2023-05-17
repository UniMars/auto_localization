import html
import json
import logging
import os

import openai
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ChatTranslator:
    def __init__(self, language: str = "english"):
        if os.path.exists('.env'):
            load_dotenv(dotenv_path='.env')
        elif os.path.exists('../../.env'):
            load_dotenv(dotenv_path='../../.env')
        else:
            logging.error("未找到.env文件")
            exit(1)
        self._api_key = os.environ.get('OPENAI_API_KEY')
        assert self._api_key, "OPENAI_API_KEY is not set"
        openai.api_key = self._api_key

        self._model = os.environ.get('OPENAI_MODEL')
        if not self._model:
            self._model = "gpt-3.5-turbo"

        self._temperature = float(os.environ.get('OPENAI_TEMPERATURE'))
        self._language = language
        self._rules = r"""
            2. Rule
                - The format of the answer is {{"message":200,"content":"$"}} and replace $ with what you translate.
                - If you don't know the language you need to translate to, the format of the answer is {{"message":404,"content":"unknown language"\}}
                - If the sentence contains any punctuation, just keep it in the same place in the translation
                - If the sentence contains any line break, just keep it in the same place in the translation and don't replace it to space.
                - If the sentence contains any special symbols like \n or &#x0a; or '&quot;', just keep it in the same place in the translation. 
                - If the sentence contains any special symbols like '$\\n$' or anything else you don't understand, just keep it in the same place in the translation.
                - The translation should be natural, fluent and brief. The structure of the sentence should be the same as the original one."""
        self._instruction = self.generate_instruction(self, language)
        self._test_sentence = r"""
                小提示：\n\n
                1. 请在有“开始行动”按钮的界面再使用本功能；\n\n
                2. 使用好友助战可以关闭“自动编队”，手动选择干员后开始；\n\n
                3. 模拟悖论需要关闭“自动编队”，并选好技能后处于“开始模拟”按钮的界面再开始；\n\n
                4. 保全派驻 在 resource/copilot 文件夹下内置了多份作业。\n
                请手动编队后在“开始部署”界面开始（可配合“循环次数”使用）\n\n
                5. 现已支持视频识别，请将攻略视频文件拖入后开始。\n
                需要视频分辨率为 16:9，无黑边、模拟器边框、异形屏矫正等干扰元素\n\n
                """

    def translate(self, sentence: str = None, target_language: str = None, model=None, temperature: float = None):
        # TODO 添加对话长度限制 添加代理
        try:
            if sentence is None:
                sentence = self._test_sentence
            if target_language is not None:
                self.set_language(target_language)
            if model is None:
                model = self._model
            if temperature is None:
                temperature = self._temperature

            new_sentence = html.unescape(sentence).replace(r'\n', r'$\\n$')
            completion = openai.ChatCompletion.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": self._instruction},
                    {"role": "user", "content": new_sentence},
                ]
            )
            msg = completion['choices'][0]['message']['content']
            msg_json = json.loads(msg)
        except Exception as _:
            logging.error(f"{type(_).__name__}: {_}")
            return None
        else:
            match msg_json['message']:
                case 200:
                    # logging.info(f"translate success")
                    content = msg_json['content'].replace(r'$\\n$', '\n').replace(r'$\n$', '\n').replace('$\n$', '\n')
                    return content
                case 404:
                    logging.error(f"translate error: {msg_json['content']}")
                    return None
                case _:
                    logging.error(f"translate error: {msg_json}")
                    return None

    def set_language(self, language):
        self._language = language
        self._instruction = self.generate_instruction(self, language)

    def get_language(self):
        return self._language

    @staticmethod
    def generate_instruction(self, language):
        return fr"""
            1. Role
                - you are a translator, translate everything i give into {language}.
            """ + self._rules

    def add_rules(self, rules: str):
        self._rules += """
                - """ + rules.strip()
        self._instruction = self.generate_instruction(self, self._language)

    def get_instruction(self):
        return self._instruction

# if __name__ == '__main__':
#     a = ChatTranslator()
#     a.translate()
#     print()
