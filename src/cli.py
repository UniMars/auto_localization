import argparse
import logging
import os

from src.translate import ChatTranslator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def initiate(args):
    logging.info(f"initiate project{args}")
    ct = ChatTranslator()
    res = ct.translate()
    logging.info(res)


def update(args):
    logging.info("update project")


def cli():
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("OPENAI_API_KEY=\nOPENAI_MODEL=\n")
    parser = argparse.ArgumentParser(description="My project command line tool.")
    subparsers = parser.add_subparsers()

    parser_initiate = subparsers.add_parser('initiate', help='initiate a project')
    parser_initiate.set_defaults(func=initiate)
    parser_initiate.add_argument("-a", "--arg", help="argument")

    parser_update = subparsers.add_parser('update', help='update the project')
    parser_update.set_defaults(func=update)
    parser_update.add_argument("-a", "--arg", help="argument")

    args = parser.parse_args()
    args.func(args)
