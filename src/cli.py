import argparse
import logging
import os
from copy import deepcopy
from shutil import copy
from typing import Union

from dotenv import load_dotenv

from src.file_loader.xaml_load import XamlParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def initiate():
    logging.info("initiate project")
    copy('./copy.env', '.env')
    with open('./copy.env', 'r') as f:
        content = f.read()
    api_key = input("please input openai api key:")
    local_path = input("please input localization path:")
    content.replace('OPENAI_API_KEY=\n', f'OPENAI_API_KEY={api_key}\n')
    content.replace('LOCALIZATION_PATH=\n', f'LOCALIZATION_PATH={local_path}\n')
    with open(".env", "w") as f:
        f.write(content)


def create(args):
    root_path = os.getenv("LOCALIZATION_PATH")
    assert root_path, "LOCALIZATION_PATH is not set"
    zh_cn_path = os.path.join(root_path, "zh-cn.xaml")
    en_us_path = os.path.join(root_path, "en-us.xaml")
    zh_tw_path = os.path.join(root_path, "zh-tw.xaml")
    ja_jp_path = os.path.join(root_path, "ja-jp.xaml")
    ko_kr_path = os.path.join(root_path, "ko-kr.xaml")
    logging.info(f"create project{args}")
    if args.force:
        logging.info("force create")
        generate_force(args.test, (zh_cn_path, en_us_path, zh_tw_path, ja_jp_path, ko_kr_path))
    else:
        logging.info("no force create")
        generate_compare()
        # logging.info(res)


def update(args):
    logging.info("update project")
    root_path = os.getenv("LOCALIZATION_PATH")
    assert root_path, "LOCALIZATION_PATH is not set"
    zh_cn_path = os.path.join(root_path, "zh-cn.xaml")
    zh_cn_new_path = os.path.join(root_path, "zh-cn_new.xaml")
    en_us_path = os.path.join(root_path, "en-us.xaml")
    zh_tw_path = os.path.join(root_path, "zh-tw.xaml")
    ja_jp_path = os.path.join(root_path, "ja-jp.xaml")
    ko_kr_path = os.path.join(root_path, "ko-kr.xaml")
    translate_update(args.test, (zh_cn_path, zh_cn_new_path, en_us_path, zh_tw_path, ja_jp_path, ko_kr_path))


def generate_force(test, paths: Union[list, tuple, set]):
    zh_cn_path, en_us_path, zh_tw_path, ja_jp_path, ko_kr_path = paths
    zh_cn_parser = XamlParser(zh_cn_path)
    en_us_parser = XamlParser(en_us_path)

    # 生成中文翻译
    zh_cn_parser.translate_force(zh_tw_path, skip_translate=test)
    zh_cn_parser.translate_force(en_us_path, skip_translate=test)
    en_us_parser.translate_force(ja_jp_path, skip_translate=test)
    en_us_parser.translate_force(ko_kr_path, skip_translate=test)
    logging.info("generate force done")


def generate_compare(test, paths: Union[list, tuple, set]):
    zh_cn_path, en_us_path, zh_tw_path, ja_jp_path, ko_kr_path = paths
    zh_cn_parser = XamlParser(zh_cn_path)
    en_us_parser = XamlParser(en_us_path)
    zh_tw_parser = XamlParser(zh_tw_path)
    ja_jp_parser = XamlParser(ja_jp_path)
    ko_kr_parser = XamlParser(ko_kr_path)
    zh_tw_parser.translate_compare(zh_cn_parser, skip_translate=test)
    en_us_parser.translate_compare(zh_cn_parser, skip_translate=test)
    ja_jp_parser.translate_compare(en_us_parser, skip_translate=test)
    ko_kr_parser.translate_compare(en_us_parser, skip_translate=test)
    logging.info("generate compare done")


def translate_update(test, paths: Union[list, tuple, set]):
    # TODO: 调用git获取中文新旧版本
    zh_cn_path, zh_cn_new_path, en_us_path, zh_tw_path, ja_jp_path, ko_kr_path = paths
    zh_cn_parser = XamlParser(zh_cn_path)
    zh_cn_new_parser = XamlParser(zh_cn_new_path)
    en_us_parser = XamlParser(en_us_path)
    en_us_old_parser = deepcopy(en_us_parser)
    zh_tw_parser = XamlParser(zh_tw_path)
    ja_jp_parser = XamlParser(ja_jp_path)
    ko_kr_parser = XamlParser(ko_kr_path)
    zh_tw_parser.update_translate(zh_cn_parser, zh_cn_new_parser, skip_translate=test)
    en_us_parser.update_translate(zh_cn_parser, zh_cn_new_parser, skip_translate=test)
    en_us_new_parser = XamlParser(en_us_path)
    ja_jp_parser.update_translate(en_us_old_parser, en_us_new_parser, skip_translate=test)
    ko_kr_parser.update_translate(en_us_old_parser, en_us_new_parser, skip_translate=test)
    logging.info("update done")


def cli():
    logging.debug(os.path.abspath('.env'))
    load_dotenv(dotenv_path='.env')
    parser = argparse.ArgumentParser(description="一个用于自动翻译本地化目录下不同语言文档的命令行工具。")
    subparsers = parser.add_subparsers()
    parser_init = subparsers.add_parser('init', help='初始化工具')
    parser_init.set_defaults(func=initiate)

    parser_create = subparsers.add_parser('create', help='初始化其他语言的文档,可选参数：-f --force, -t --test')
    parser_create.set_defaults(func=create)
    parser_create.add_argument("-f", "--force", action="store_true", help="强制覆盖已有的部分")
    parser_create.add_argument("-t", "--test", action="store_true", help="测试更新情况（跳过chatgpt）")

    parser_update = subparsers.add_parser('update', help='更新本地化翻译,可选参数：-t --test')
    parser_update.set_defaults(func=update)
    parser_update.add_argument("-t", "--test", action="store_true", help="测试更新情况（跳过chatgpt）")

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    print()
