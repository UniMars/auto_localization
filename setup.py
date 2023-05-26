from setuptools import setup, find_packages

setup(
    name='AutoLocalization',
    version='1.0',
    url='',
    license='',
    author='noctboat',
    author_email='65664032+UniMars@users.noreply.github.com',
    description='A tool to translate doc into different languages.',
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            'auto_localization = auto_localization.cli:cli',
        ],
    },
    install_requires=[
        'lxml~=4.9.2',
        'openai~=0.27.7',
        'python-dotenv~=1.0.0',
        'Cython>=0.29.25',
        'cchardet~=2.1.7',
        'xmldiff>=2.6.3',
        'opencc~=1.1.1'
    ],
    python_requires='>3.10',

)
