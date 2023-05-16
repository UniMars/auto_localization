import argparse
import logging
import os

from dotenv import load_dotenv

from src.translate import ChatTranslator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def initiate(args):
    logging.info("initiate project")
    logging.debug(os.path.abspath('.env'))
    load_dotenv(dotenv_path='.env')
    if not os.environ.get('OPENAI_API_KEY'):
        api_key = input("请输入openai api key:")
        with open(".env", "w") as f:
            f.write(f"# chatgpt设置\nOPENAI_API_KEY={api_key}\nOPENAI_MODEL=gpt-3.5-turbo\nOPENAI_TEMPERATURE=0.7")


def create(args):
    logging.info(f"create project{args}")
    ct = ChatTranslator()
    res = ct.translate()
    logging.info(res)


def update(args):
    logging.info("update project")


def cli():
    parser = argparse.ArgumentParser(description="一个用于自动翻译本地化目录下不同语言文档的命令行工具。")
    subparsers = parser.add_subparsers()
    parser_init = subparsers.add_parser('init', help='初始化工具')
    parser_init.set_defaults(func=initiate)

    parser_create = subparsers.add_parser('create', help='初始化其他语言的文档')
    parser_create.set_defaults(func=create)
    parser_create.add_argument("-a", "--arg", help="argument")

    parser_update = subparsers.add_parser('update', help='更新本地化翻译')
    parser_update.set_defaults(func=update)
    parser_update.add_argument("-a", "--arg", help="argument")

    args = parser.parse_args()
    args.func(args)
