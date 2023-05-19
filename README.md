# auto_localization

这个命令行工具可以帮助您自动翻译本地化目录中的不同语言文档。

## TODO

自动本地化有几点要求看看能不能做到：

1. 不要破坏缩进（包括空行不带空格）
2. `<ResourceDictionary x:Uid="KeyName">` 如果能在资源字典找到Uid对应的Key，把对应的Value作为注释写入，像这样（注意注释中的空格）：
    ```xml
            <!--  设置  -->
    <ResourceDictionary x:Uid="Settings">
    </ResourceDictionary>
    ```
3. 由于字典被拆分了，重复的键要交给脚本检查
4. 因为zh-cn可能会混入一些中文梗，所以ja-jp、ko-kr尽量由en-us翻译

    ```code
    check duplicate Key()
    if exist duplicate Key:
        throw (or raise) an exception
    
    zh-cn -> zh-tw
    if exist en-us:
        en-us -> ja-jp
        en-us -> ko-kr
    else:
        zh-cn -> ja-jp
        zh-cn -> ko-kr
        zh-cn -> en-us
    ```

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