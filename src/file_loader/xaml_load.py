import os
import re
from copy import deepcopy

from cchardet import detect
from lxml import etree
from xmldiff import main
from xmldiff.actions import UpdateTextIn, InsertComment, UpdateTextAfter

from src.file_loader.diff import patch_tree
from src.translator.translate import ChatTranslator


# TODO 打印日志显示翻译进度
def judge_encoding(file):
    with open(file, 'rb') as _:
        content = _.read()
        result = detect(content)
        return result['encoding']


def parse_lang_str(doc_path):
    lang_str = os.path.basename(doc_path)
    match lang_str:
        case s if 'zh-cn' in s:
            return "Chinese (Simplified)"
        case s if 'zh-tw' in s:
            return "Chinese (Traditional)"
        case s if 'en-us' in s:
            return "English"
        case s if 'ja-jp' in s:
            return "Japanese"
        case s if 'ko-kr' in s:
            return "Korean"
        case _:
            raise ValueError('wrong language input')

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
    """
    XamlParser类，用于解析xaml文件

    """

    def __init__(self, parse_type=0, file=None, xaml_string=None, language=None, encoding='utf-8'):
        """
        初始化XamlParser类
        :param parse_type: 0表示从文件解析，1表示从字符串解析
        :param file: 从文件解析时，传入文件路径
        :param xaml_string: 从字符串解析时，传入xaml字符串
        :param language: 从字符串解析时，传入语言
        :param encoding: 从字符串解析时，传入编码
        """
        if parse_type == 0:
            self._file_path, self.__encoding, self.__language, xaml_string = self.__from_file(file)
        elif parse_type == 1:
            assert language is not None, 'language must be specified when parse_type is 1'
            self._file_path, self.__encoding, self.__language = file, encoding, language
        else:
            raise ValueError('parse_type must be 0 or 1')
        xaml_string = xaml_string.replace('&#x0a;', '\\n')
        self.__root = etree.fromstring(xaml_string)
        # 获取命名空间
        self.__nsmap = self.__root.nsmap
        self.__default_namespace = self.__nsmap.get(None)
        self.__x_ns = self.__nsmap.get('x')
        self.__x_uid_ns, self.__x_key_ns = f'{{{self.__x_ns}}}Uid', f'{{{self.__x_ns}}}Key'
        self.__merged_node = self.__root.find('./ResourceDictionary.MergedDictionaries', namespaces=self.__nsmap)
        self.__cp_root = self.copy_node(self.__root, cp_text=True)

        self.__cp_merged_node = self.copy_node(self.__merged_node, cp_text=True)
        self.__cp_root.append(self.__cp_merged_node)
        self.__gen_cp_tree_by_traverse(element=self.__root, current_cp_node=self.__cp_root)

    def __from_file(self, file):
        assert os.path.exists(file), 'file not exists'
        encoding = judge_encoding(file)
        language = parse_lang_str(file)
        with open(file, 'r', encoding=encoding) as f:
            content = f.read()
        return file, encoding, language, content

    def __gen_cp_tree_by_traverse(self, element, current_cp_node):
        for child in element:
            if child.tag == etree.Comment:
                # 注释节点
                parent = child.getparent()
                if parent is None:
                    continue
                children = list(parent)
                index = children.index(child)
                if parent.tag == f'{{{self.__default_namespace}}}ResourceDictionary' and index == 0:
                    continue
                if index == 0:
                    # 注释节点为第一个节点
                    cp_comment = self.copy_node(child, cp_text=False)
                    current_cp_node.append(cp_comment)
                    continue
                cp_comment = self.copy_node(child, cp_text=False)
                prev_node = children[index - 1]
                prev_cp_node = current_cp_node[index - 1]
                assert prev_node.tag == prev_cp_node.tag and prev_node.attrib == prev_cp_node.attrib, "前节点类型不一致"
                current_cp_node.append(cp_comment)
                continue

            cp_node = self.copy_node(child)
            if child.tag == f'{{{self.__default_namespace}}}ResourceDictionary.MergedDictionaries':
                # 次根 MergedDictionaries: 遍历后退出循环
                current_cp_node = self.__cp_merged_node
                self.__gen_cp_tree_by_traverse(child, current_cp_node=current_cp_node)
                break
            elif child.tag == f'{{{self.__default_namespace}}}ResourceDictionary':
                # resource dictionary uid组
                cp_node.text = child.text
                current_cp_node.append(cp_node)

                # 添加说明注释
                chat = ChatTranslator(language=self.language, base_language="english")
                uid = child.get(self.__x_uid_ns)
                new_comment = etree.Comment(f"${uid}:")
                # new_comment.text += self.language + ' '
                # new_comment.text += chat.translate(uid)
                new_comment.tail = child.text
                if child[0].tag != etree.Comment:
                    child.insert(0, new_comment)
                else:
                    child[0].text = new_comment.text
                cp_comment = self.copy_node(new_comment, cp_text=True)
                cp_node.insert(0, cp_comment)
                self.__gen_cp_tree_by_traverse(child, current_cp_node=cp_node)
            elif child.get(self.__x_key_ns) is not None:
                # 正常节点
                current_cp_node.append(cp_node)
            else:
                current_cp_node.append(cp_node)
                self.__gen_cp_tree_by_traverse(child, current_cp_node=cp_node)
        return current_cp_node

    @staticmethod
    def copy_node(node, cp_text=False):
        if node.tag == etree.Comment:
            cp_node = etree.Comment(node.text) if cp_text else etree.Comment("")
            cp_node.tail = node.tail
        else:
            cp_node = etree.Element(node.tag, attrib=node.attrib, nsmap=node.nsmap)
            cp_node.text = node.text if cp_text else ""
            cp_node.sourceline = node.sourceline
            cp_node.tail = node.tail
        return cp_node

    def write_xaml(self, tree=None, file_path=None):
        if tree is None:
            tree = self.tree
        if file_path is None:
            file_path = self._file_path
        if file_path is None:
            return False
        xaml_data = etree.tostring(tree, pretty_print=True, encoding=self.__encoding)
        # xaml_data = html.unescape(xaml_data.decode(self.__encoding))
        xaml_data = xaml_data.decode(self.__encoding)
        with open(file_path, 'w', encoding=self.__encoding) as _:
            _.write(xaml_data)
        return True

    def compare_structure(self, compare_parser):
        """
        比较两个xaml结构，比较时忽略类似<ResourceDictionary x:Uid="xxx">下的首个注释节点
        :param compare_parser:
        :return: 如果结构一致返回True，否则返回False
        """
        this_tree = self.cp_tree
        compare_tree = compare_parser.cp_tree
        assert self.x_key_ns == compare_parser.x_key_ns, f"{self.language} 和 {compare_parser.language}x:Key命名空间不一致"
        assert self.x_uid_ns == compare_parser.x_uid_ns, f"{self.language} 和 {compare_parser.language}x:Uid命名空间不一致"
        pt = re.compile(r'/\*/\*/\*\[\d*]/comment\(\)\[1]')
        uniqueattrs = [self.x_key_ns, self.x_uid_ns]
        res = main.diff_trees(this_tree, compare_tree, diff_options={
            'F': 0.1,
            'ratio_mode': 'accurate',
            'uniqueattrs': uniqueattrs})
        for i in res:
            if type(i).__name__ == 'UpdateTextIn' and pt.search(i.node):
                continue
            return False
        return True

    def translate_force(self, target_path, skip_translate=False):
        """
        强制输出本文件到目标文件的翻译，完成后本文件也会更新
        :param target_path: 输出的目标文件路径
        :param skip_translate: 是否跳过chatgpt翻译
        :return:
        """
        target_language = parse_lang_str(target_path)
        output_tree = deepcopy(self.cp_tree)
        chat = ChatTranslator(language=target_language, base_language=self.language)
        for i in self.__merged_node.findall('.//s:String[@x:Key]', namespaces=self.__nsmap):
            key = i.get(self.__x_key_ns)
            node = output_tree.find(f'.//s:String[@x:Key="{key}"]', namespaces=self.__nsmap)
            node.text = i.text if skip_translate else chat.translate(i.text)
        self.write_xaml(output_tree, target_path)
        self.write_xaml()

    def translate_compare(self, compare_parser, skip_translate=False):
        """
        输出本文件到目标文件的翻译，若目标文件存在与本文件相同的节点，则跳过该节点，完成后本文件也会更新
        :param compare_parser: 目标文件的XamlParser
        :param skip_translate: 是否跳过chatgpt翻译
        :return: 返回翻译后的Xaml lxml树
        """
        target_cp_tree = self.cp_tree
        base_cp_tree = compare_parser.cp_tree
        assert self.nsmap == compare_parser.nsmap, f"{self.language} 和 {compare_parser.language}命名空间不一致"
        assert self.x_key_ns == compare_parser.x_key_ns, f"{self.language}和{compare_parser.language}x:Key命名空间不一致"
        assert self.x_uid_ns == compare_parser.x_uid_ns, f"{self.language}和{compare_parser.language}x:Uid命名空间不一致"
        ns = self.nsmap
        ns.pop(None)
        uniqueattrs = [self.x_key_ns, self.x_uid_ns]
        chat = ChatTranslator(language=self.language, base_language=compare_parser.language)
        res = main.diff_trees(target_cp_tree, base_cp_tree, diff_options={
            'F': 0.1,
            'ratio_mode': 'accurate',
            'uniqueattrs': uniqueattrs})
        new_action = []
        comment_list = []
        for i in res:
            if type(i).__name__ == 'MoveNode' and 'comment()' in i.node:
                search_result = compare_parser.tree.xpath(i.target, namespaces=ns)
                assert len(search_result) == 1, f"xpath: {search_result} 搜索结果数量不为1"
                str_node = search_result[0][i.position]
                assert str_node.tag == etree.Comment, f"xpath: {search_result} 搜索结果不为comment"
                node_position = "{}/comment()[{}]".format(i.target,
                                                          len(str_node.xpath('preceding-sibling::comment()')) + 1)
                new_action.append(InsertComment(i.target, i.position, str_node.text))
                new_action.append(UpdateTextAfter(node_position, str_node.tail))
                comment_list.append(i.node)
            elif type(i).__name__ == 'UpdateTextIn':
                if 'comment()' in i.node:
                    continue
                search_result = compare_parser.tree.xpath(i.node, namespaces=ns)
                assert len(search_result) == 1, f"xpath: {search_result} 搜索结果数量不为1"
                str_node = search_result[0]
                text = str_node.text if skip_translate else chat.translate(str_node.text)
                new_action.append(UpdateTextIn(i.node, text))
            elif type(i).__name__ == 'InsertComment':
                if i.target + "/comment()" in comment_list[0]:
                    comment_list.pop(0)
                    continue
                search_result = compare_parser.tree.xpath(i.target, namespaces=ns)
                assert len(search_result) == 1, f"xpath: {search_result} 搜索结果数量不为1"
                str_node = search_result[0][i.position]
                assert str_node.tag == etree.Comment, f"xpath: {search_result} 搜索结果不为comment"
                node_position = "{}/comment()[{}]".format(i.target,
                                                          len(str_node.xpath('preceding-sibling::comment()')) + 1)
                new_action.append(InsertComment(i.target, i.position, str_node.text))
                new_action.append(UpdateTextAfter(node_position, str_node.tail))
            else:
                new_action.append(i)
        assert len(comment_list) == 0, f"comment剩余{comment_list}"
        final_tree = patch_tree(new_action, self.tree, nsmap=ns)
        # final_tree = main.patch_tree(new_action, self.tree)
        compare_parser.write_xaml()
        self.write_xaml(final_tree, self._file_path)
        return final_tree

    def update_translate(self, compare_old_parser, compare_new_parser, skip_translate=False):
        """
        将比较新旧两个文件的更新，并将更新同步到本文件，若本文件与旧文件结构不同，则会与旧文件调用translate_compare
        :param compare_old_parser: 旧文件的XamlParser
        :param compare_new_parser: 新文件的XamlParser
        :param skip_translate: 是否跳过chatgpt翻译
        :return: 返回翻译后的Xaml lxml树
        """
        compare_old_tree = compare_old_parser.merged_root_tree
        if not self.compare_structure(compare_old_parser):
            target_tree = self.translate_compare(compare_old_parser, skip_translate=skip_translate)
        else:
            target_tree = self.cp_tree
        compare_new_tree = compare_new_parser.merged_root_tree
        assert compare_old_parser.nsmap == compare_new_parser.nsmap, \
            f"old {compare_old_parser.language}和 new {compare_new_parser.language}命名空间不一致"
        assert compare_old_parser.x_key_ns == compare_new_parser.x_key_ns, \
            f"old {compare_old_parser.language}和 new {compare_new_parser.language}x:Key命名空间不一致"
        assert compare_old_parser.x_uid_ns == compare_new_parser.x_uid_ns, \
            f"old {compare_old_parser.language}和 new {compare_new_parser.language}x:Uid命名空间不一致"

        chat = ChatTranslator(language=self.language, base_language=compare_new_parser.language)
        ns = self.nsmap
        ns.pop(None)
        uniqueattrs = [self.x_key_ns, self.x_uid_ns]
        res = main.diff_trees(compare_old_tree, compare_new_tree, diff_options={
            'F': 0.1,
            'ratio_mode': 'accurate',
            'uniqueattrs': uniqueattrs})
        new_actions = []
        for i in res:
            if type(i).__name__ == 'UpdateTextIn':
                if i.node.endswith('comment()[1]') and i.text[0] == '$':
                    continue
                elif 's:String' in i.node:
                    text = i.text if skip_translate else chat.translate(i.text)
                    new_actions.append(UpdateTextIn(i.node, text))
                else:
                    new_actions.append(i)
            else:
                new_actions.append(i)

        final_tree = patch_tree(new_actions, target_tree, nsmap=ns)
        compare_new_parser.write_xaml()
        self.write_xaml(final_tree)
        return final_tree

    @property
    def cp_tree(self):
        return self.__cp_root

    @property
    def cp_merged_node(self):
        return self.__cp_merged_node

    @property
    def tree(self):
        return self.__root

    @property
    def merged_node(self):
        return self.__merged_node

    @property
    def nsmap(self):
        return deepcopy(self.__nsmap)

    @property
    def x_uid_ns(self):
        return self.__x_uid_ns

    @property
    def x_key_ns(self):
        return self.__x_key_ns

    @property
    def merged_root_tree(self):
        root = self.copy_node(self.__root, cp_text=True)
        root.append(deepcopy(self.__merged_node))
        return root

    @property
    def language(self):
        return self.__language


# class XamlParser1:
#     def __init__(self, file="../sample/zh-cn_new.xaml"):
#         self._file_path = file
#         self.encoding = judge_encoding(file)
#         self._tree = etree.parse(file)
#         self.root_tree = self._tree.getroot()
#         self.__merged_node = None
#
#         # 获取命名空间
#         self.__nsmap = self.root_tree.nsmap
#         self.__default_namespace = self.__nsmap.get(None)
#         self._x_namespace = self.__nsmap.get('x')
#         self._x_key = f'{{{self._x_namespace}}}Key'
#         self._x_uid = f'{{{self._x_namespace}}}Uid'
#         self._key_list = []
#         # self._uid_list = []
#         self.copy_tree = self.copy_node(self.root_tree, cp_text=True)
#         self.resource_dict = {
#             "": {"uid": "",
#                  "node": self.root_tree,
#                  "node_list": [],
#                  "key_list": [],
#                  "comment_list": []
#                  }
#         }
#         self.gen_resource_dict_by_traverse(self.root_tree, "", self.copy_tree)
#
#     def gen_resource_dict_by_traverse(self, element, current_uid, current_cp_node):
#         """
#         生成资源字典
#         :param element: 待遍历的根节点
#         :param current_uid: 当前的uid值
#         :param current_cp_node: 当前的父节点
#         :return: {
#                     keys : 所有的uid,
#                     values:{
#                             "uid": resource dictionary 的 uid 值
#                             'cp_node': 该 resource dictionary 对应生成的注释节点,
#                             "node": resource dictionary 节点,
#                             "node_list": [{
#                                         "uid": 当前 resource dictionary 的 uid 值,
#                                         "key": 叶子节点的 key 值,
#                                         "value": 内容文本,
#                                         'cp_node': 生成的对应复制节点,
#                                         'node': 叶子节点, },......],
#                             'key_list': [],
#                             'comment_list': []
#                     }
#                 }
#         """
#         for child in element:
#             if child.tag == etree.Comment:
#                 # 注释节点
#                 prev_node_list = self.resource_dict[current_uid]['node_list']
#                 if prev_node_list:
#                     prev_node = prev_node_list[-1]['node']
#                     prev_node.tail += child.text.count('\n') * '\n' + child.tail
#                 self.resource_dict[current_uid]['comment_list'].append(child)
#                 continue
#
#             cp_node = self.copy_node(child)
#             if child.tag == f'{{{self.__default_namespace}}}ResourceDictionary.MergedDictionaries':
#                 # 次根 MergedDictionaries: 遍历后退出循环
#                 cp_node.tail += '\n'
#                 cp_node.text = child.text
#                 self.__merged_node = cp_node
#                 current_cp_node.append(cp_node)
#                 current_cp_node = cp_node
#                 self.gen_resource_dict_by_traverse(child, current_uid, current_cp_node)
#                 break
#             elif child.tag == f'{{{self.__default_namespace}}}ResourceDictionary':
#                 # resource dictionary with uid组
#                 # self._uid_list.append(uid)
#                 current_uid = child.get(self._x_uid)
#                 # merged_node = current_cp_node
#                 comment_node = etree.Comment(f"${current_uid}:")
#                 comment_node.tail = child.text
#                 cp_node.text = child.text
#                 cp_node.insert(0, comment_node)
#                 current_cp_node.append(cp_node)
#                 self.resource_dict[current_uid] = {"uid": current_uid,
#                                                    'cp_node': comment_node,
#                                                    "node": child,
#                                                    "node_list": [],
#                                                    'key_list': [],
#                                                    'comment_list': []}
#                 self.gen_resource_dict_by_traverse(child, current_uid, cp_node)
#                 # current_cp_node = merged_node
#             else:
#                 # 正常节点
#                 key = child.get(self._x_key)
#                 if key is None:
#                     raise KeyError(f"key is None, tag: {child.tag}")
#                 current_cp_node.append(cp_node)
#                 self.resource_dict[current_uid]['node_list'].append({
#                     "uid": current_uid,
#                     "key": key,
#                     "value": child.text,
#                     'cp_node': cp_node,
#                     'node': child, })
#                 self.resource_dict[current_uid]['key_list'].append(key)
#                 self._key_list.append(key)
#         return self.resource_dict
#
#     @staticmethod
#     def copy_node(child, cp_text=False):
#         node = etree.Element(child.tag, attrib=child.attrib, nsmap=child.nsmap)
#         node.sourceline = child.sourceline
#         node.tail = child.tail
#         node.text = child.text if cp_text else ""
#         return node
#
#     def search_nodes(self, key, uid=None):
#         """
#         根据key值查找节点
#         :param key: x键
#         :param uid: 所属的uid，如果为None，则遍历所有的uid
#         :return: 返回node_dict
#         """
#         if uid is None:
#             for uid, resource in self.resource_dict.items():
#                 node_list = resource['node_list']
#                 for node in node_list:
#                     if node['key'] == key:
#                         yield node
#             # return res
#         if uid not in self.resource_dict.keys():
#             return None
#         else:
#             node_list = self.resource_dict[uid]['node_list']
#             for node in node_list:
#                 if node['key'] == key:
#                     yield node
#
#     def search_resource_dict_by_uid(self, uid):
#         if uid not in self.resource_dict.keys():
#             return None
#         return self.resource_dict[uid]
#
#     @property
#     def duplicate_key(self):
#         # 查找重复的key
#         counter = Counter(self._key_list)
#         # Find out which items appear more than once
#         return [item for item, count in counter.items() if count > 1]
#
#     @property
#     def key_list(self):
#         if len(self.duplicate_key):
#             raise KeyError(f"key is duplicate: {self.duplicate_key}")
#         return set(self._key_list)
#
#     def create_new_resource_node(self, uid, index=-1):
#         if uid in self.resource_dict.keys():
#             return self.resource_dict[uid]
#
#         # 获得上一个resource_dictionary节点的index
#         prev_u = [i for i in self.resource_dict.keys()][index]
#         prev_node = self.resource_dict[prev_u]['node']
#
#         new_resource_node = self.copy_node(prev_node)
#         comment_node = etree.Comment(f"${uid}:")
#         comment_node.tail = prev_node.text
#         new_resource_node.insert(0, comment_node)
#
#         resource_dictionary = {"uid": uid,
#                                'cp_node': comment_node,
#                                "node": new_resource_node,
#                                "node_list": [],
#                                'key_list': [],
#                                'comment_list': [comment_node]}
#         self.resource_dict[uid] = resource_dictionary
#         self.__merged_node.insert(index, new_resource_node)
#         return resource_dictionary


def t(base_tree, target_tree, action):
    match action:
        case a if hasattr(a, 'node'):
            action.node = "" + action.node
        case a if hasattr(a, 'target'):
            action.target = "" + action.target
        case "UpdateTextIn":
            # translate
            pass
        case "UpdateTextAfter":
            # ...
            pass
        case "UpdateAttrib":
            pass
        case "InsertComment":
            # skip
            pass
        case _:
            pass


if __name__ == '__main__':
    zh_parser = XamlParser(parse_type=0, file='../sample/zh-cn.xaml')
    zh_new_parser = XamlParser(parse_type=0, file='../sample/zh-cn_new.xaml')
    # zh_new_parser = XamlParser('../sample/zh-cn_new.xaml')
    en_parser = XamlParser(parse_type=0, file='../sample/en-us.xaml')
    # en_parser.write_xaml(file_path='../sample/en-us_copy2.xaml')
    en_parser.translate_compare(zh_parser, skip_translate=True)
    en_parser.update_translate(zh_parser, zh_new_parser, skip_translate=True)
    # en_parser = XamlParser('../sample/en-us_copy2.xaml')
    print()
    # # zh_parser.translate('en-us')
    # # zh_cp_parser = XamlParser('../sample/zh-cn_copy.xaml')
    # target_parser = XamlParser('../sample/en-us.xaml')
    # translate_compare()
    print()
