from lxml import etree

print()


def load_xaml(file):
    tree = etree.parse(file)
    root = tree.getroot()

    # 获取命名空间
    namespaces = root.nsmap
    xaml_namespace = namespaces.get('x')
    xaml_key = '{' + xaml_namespace + '}Key'

    resource_dict = {}
    comment_list = []
    for element in root:
        if isinstance(element, etree._Comment):
            print(f"comment tag: {element.text}")
            comment_list.append(element.text.strip())
        else:
            key = element.get(f'{xaml_key}Key')
            if key is not None:
                resource_dict[key] = element.text
                print(f"key: {key}, value: {element.text}")
            else:
                print(f"tag: {element.tag}, text: {element.text}")
    return resource_dict


xaml_file = r'D:\Programs\Code\cpp\projects\MaaAssistantArknights\src\MaaWpfGui\Res\Localizations\zh-cn.xaml'
resource_dict1 = load_xaml(xaml_file)

print(resource_dict1)  # 输出：{'Settings': '设置'}
