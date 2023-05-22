import subprocess


def get_latest_file_content(file_path='./cli.py', encoding='utf-8'):
    result = subprocess.run(['git', 'show', f'HEAD:{file_path}'], stdout=subprocess.PIPE)
    return result.stdout.decode(encoding)


if __name__ == '__main__':
    print(get_latest_file_content('./cli.py'))
