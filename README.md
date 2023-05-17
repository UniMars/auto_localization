# auto_localization

这个命令行工具可以帮助您自动翻译本地化目录中的不同语言文档。

## 配置
在使用前，您需要配置OpenAI API密钥。运行init子命令将会提示您输入API密钥，并将其存储在.env文件中。

## 功能
### 初始化工具
要初始化工具，请运行以下命令：

```bash
python main.py init
```
### 创建其他语言的文档
要为其他语言创建文档，请运行以下命令：

```bash
python main.py create
```
如果要强制覆盖已有的部分，请使用-f或--force标志：

```bash
python main.py create -f
```
### 更新本地化翻译
要更新本地化翻译，请运行以下命令：

```bash
python main.py update
```
使用-a或者--arg参数传递额外的参数：

```bash
python main.py update -a "argument"
```
## 依赖
运行
```bash
pip install -r requirements.txt
```
Enjoy!