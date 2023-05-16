import html
import json
import logging
import os

import openai
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ChatTranslator:
    def __init__(self, gpt_model="gpt-3.5-turbo"):
        load_dotenv(dotenv_path='../.env')
        self._api_key = os.environ.get('OPENAI_API_KEY')
        self._model = os.environ.get('OPENAI_MODEL')
        self._temperature = os.environ.get('OPENAI_TEMPERATURE')
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        if not self._model:
            self._model = gpt_model

    def translate(self, sentence="", target_language="english", temperature=-1):
        openai.api_key = self._api_key
        if temperature == -1:
            temperature = self._temperature
        if not temperature:
            temperature = 0.7
        rules = fr"""
            1. you are a translator, translate everything i give into {target_language}.
            2. Rule
                - The format of the answer is {{"message":200,"content":"$"}} and replace $ with what you translate.
                - If you don't know the language you need to translate to, the format of the answer is {{"message":404,"content":"unknown language"}}
                - If the sentence contains any punctuation, just keep it in the same place in the translation
                - If the sentence contains any line break, just keep it in the same place in the translation and don't replace it to space.
                - If the sentence contains any special symbols like \n or &#x0a; or '&quot;', just keep it in the same place in the translation. 
                - If the sentence contains any special symbols like '$\\n$' or anything else you don't understand, just keep it in the same place in the translation.
                - The translation should be natural, fluent and brief. The structure of the sentence should be the same as the original one. 
            """
        test_sentence = r"""
                小提示：\n\n
                1. 请在有“开始行动”按钮的界面再使用本功能；\n\n
                2. 使用好友助战可以关闭“自动编队”，手动选择干员后开始；\n\n
                3. 模拟悖论需要关闭“自动编队”，并选好技能后处于“开始模拟”按钮的界面再开始；\n\n
                4. 保全派驻 在 resource/copilot 文件夹下内置了多份作业。\n
                请手动编队后在“开始部署”界面开始（可配合“循环次数”使用）\n\n
                5. 现已支持视频识别，请将攻略视频文件拖入后开始。\n
                需要视频分辨率为 16:9，无黑边、模拟器边框、异形屏矫正等干扰元素\n\n
                """
        if not sentence:
            sentence = test_sentence
        new_sentence = html.unescape(sentence).replace(r'\n', r'$\\n$')
        completion = openai.ChatCompletion.create(
            model=self._model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": rules},
                {"role": "user", "content": new_sentence},
            ]
        )
        msg = completion['choices'][0]['message']['content']
        try:
            msg_json = json.loads(msg)
        except Exception as _:
            logging.error(f"json load error: {_}")
            return None
        match msg_json['message']:
            case 200:
                # logging.info(f"translate success")
                content = msg_json['content'].replace(r'$\\n$', '\n').replace(r'$\n$', '\n')
                return content
            case 404:
                logging.error(f"translate error: {msg_json['content']}")
                return None
            case _:
                logging.error(f"translate error: {msg_json}")
                return None


a = ChatTranslator()

a.translate()
