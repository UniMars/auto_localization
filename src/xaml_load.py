import html
from collections import Counter

from cchardet import detect
from lxml import etree


def judge_encoding(file):
    with open(file, 'rb') as _:
        content = _.read()
        result = detect(content)
        return result['encoding']

    # 深度优先遍历所有节点


def dft(element, hor_exist=lambda x: False, ver_exist=lambda x: False):
    for child in element:
        yield child
        if not ver_exist(child):
            dft(child, hor_exist=hor_exist, ver_exist=ver_exist)
        if hor_exist(child):
            break


def bft(element, hor_exist=lambda x: False, ver_exist=lambda x: False):
    node_list = []
    for child in element:
        node_list.append(child)
        yield child
        if hor_exist(child):
            break
    for node in node_list:
        if not ver_exist(node):
            bft(node, hor_exist=hor_exist, ver_exist=ver_exist)


class XamlParser:
    def __init__(self, file="../sample/zh-cn.xaml"):
        self._file_path = file
        self.encoding = judge_encoding(file)
        self._tree = etree.parse(file)
        self.root_tree = self._tree.getroot()
        self._merged_node = None

        # 获取命名空间
        self._namespaces = self.root_tree.nsmap
        self._default_namespace = self._namespaces.get(None)
        self._x_namespace = self._namespaces.get('x')
        self._x_key = f'{{{self._x_namespace}}}Key'
        self._x_uid = f'{{{self._x_namespace}}}Uid'
        self._key_list = []
        # self._uid_list = []
        self.copy_tree = self.copy_node(self.root_tree, cp_text=True)
        self.resource_dict = {
            "": {"uid": "",
                 "node": self.root_tree,
                 "node_list": [],
                 "key_list": [],
                 "comment_list": []
                 }
        }
        self.gen_resource_dict_by_traverse(self.root_tree, "", self.copy_tree)

    def gen_resource_dict_by_traverse(self, element, current_uid, current_cp_node):
        """
        生成资源字典
        :param element: 待遍历的根节点
        :param current_uid: 当前的uid值
        :param current_cp_node: 当前的父节点
        :return: {
                    keys : 所有的uid,
                    values:{
                            "uid": resource dictionary 的 uid 值
                            'cp_node': 该 resource dictionary 对应生成的注释节点,
                            "node": resource dictionary 节点,
                            "node_list": [{
                                        "uid": 当前 resource dictionary 的 uid 值,
                                        "key": 叶子节点的 key 值,
                                        "value": 内容文本,
                                        'cp_node': 生成的对应复制节点,
                                        'node': 叶子节点, },......],
                            'key_list': [],
                            'comment_list': []
                    }
                }
        """
        for child in element:
            if child.tag == etree.Comment:
                # 注释节点
                prev_node_list = self.resource_dict[current_uid]['node_list']
                if prev_node_list:
                    prev_node = prev_node_list[-1]['node']
                    prev_node.tail += child.text.count('\n') * '\n' + child.tail
                self.resource_dict[current_uid]['comment_list'].append(child)
                continue

            cp_node = self.copy_node(child)
            if child.tag == f'{{{self._default_namespace}}}ResourceDictionary.MergedDictionaries':
                # 次根 MergedDictionaries: 遍历后退出循环
                cp_node.text = child.text
                cp_node.tail += '\n'
                self._merged_node = cp_node
                current_cp_node.append(cp_node)
                current_cp_node = cp_node
                self.gen_resource_dict_by_traverse(child, current_uid, current_cp_node)
                break
            elif child.tag == f'{{{self._default_namespace}}}ResourceDictionary':
                # resource dictionary with uid组
                # self._uid_list.append(uid)  # TODO 是否必要
                current_uid = child.get(self._x_uid)
                # merged_node = current_cp_node
                comment_node = etree.Comment(f"${current_uid}:")
                comment_node.tail = child.text
                cp_node.text = child.text
                cp_node.insert(0, comment_node)
                current_cp_node.append(cp_node)
                self.resource_dict[current_uid] = {"uid": current_uid,
                                                   'cp_node': comment_node,
                                                   "node": child,
                                                   "node_list": [],
                                                   'key_list': [],
                                                   'comment_list': []}
                self.gen_resource_dict_by_traverse(child, current_uid, cp_node)
                # current_cp_node = merged_node
            else:
                # 正常节点
                key = child.get(self._x_key)
                if key is None:
                    raise KeyError(f"key is None, tag: {child.tag}")
                current_cp_node.append(cp_node)
                self.resource_dict[current_uid]['node_list'].append({
                    "uid": current_uid,
                    "key": key,
                    "value": child.text,
                    'cp_node': cp_node,
                    'node': child, })
                self.resource_dict[current_uid]['key_list'].append(key)
                self._key_list.append(key)
        return self.resource_dict

    @staticmethod
    def copy_node(child, cp_text=False):
        node = etree.Element(child.tag, attrib=child.attrib, nsmap=child.nsmap)
        node.sourceline = child.sourceline
        node.tail = child.tail
        node.text = child.text if cp_text else ""
        return node

    def search_nodes(self, key, uid=None):
        """
        根据key值查找节点
        :param key: x键
        :param uid: 所属的uid，如果为None，则遍历所有的uid
        :return: 返回node_dict
        """
        if uid is None:
            for uid, resource in self.resource_dict.items():
                node_list = resource['node_list']
                for node in node_list:
                    if node['key'] == key:
                        yield node
            # return res
        if uid not in self.resource_dict.keys():
            return None
        else:
            node_list = self.resource_dict[uid]['node_list']
            for node in node_list:
                if node['key'] == key:
                    yield node

    def search_resource_dict_by_uid(self, uid):
        if uid not in self.resource_dict.keys():
            return None
        return self.resource_dict[uid]

    @property
    def duplicate_key(self):
        # 查找重复的key
        counter = Counter(self._key_list)
        # Find out which items appear more than once
        return [item for item, count in counter.items() if count > 1]

    @property
    def key_list(self):
        if len(self.duplicate_key):
            raise KeyError(f"key is duplicate: {self.duplicate_key}")
        return set(self._key_list)

    def create_new_resource_node(self, uid, index=-1):
        if uid in self.resource_dict.keys():
            return self.resource_dict[uid]

        # 获得上一个resource_dictionary节点的index
        prev_u = [i for i in self.resource_dict.keys()][index]
        prev_node = self.resource_dict[prev_u]['node']

        new_resource_node = self.copy_node(prev_node)
        comment_node = etree.Comment(f"${uid}:")
        comment_node.tail = prev_node.text
        new_resource_node.insert(0, comment_node)

        resource_dictionary = {"uid": uid,
                               'cp_node': comment_node,
                               "node": new_resource_node,
                               "node_list": [],
                               'key_list': [],
                               'comment_list': [comment_node]}
        self.resource_dict[uid] = resource_dictionary
        self._merged_node.insert(index, new_resource_node)
        return resource_dictionary


def write_xaml(tree, file_path=None, encoding='utf-8'):
    if file_path is None:
        file_path = '../sample/zh-cn_copy.xaml'
    xaml_data = etree.tostring(tree, pretty_print=True, encoding=encoding)
    xaml_data = html.unescape(xaml_data.decode(encoding))
    with open(file_path, 'w', encoding=encoding) as _:
        _.write(xaml_data)


if __name__ == '__main__':
    resource_dict1 = XamlParser()
    write_xaml(resource_dict1.copy_tree)
    # a = resource_dict1.find_duplicate_key()
    print(resource_dict1)  # 输出：{'Settings': '设置'}
