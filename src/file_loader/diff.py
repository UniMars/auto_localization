from copy import deepcopy

from lxml import etree
from xmldiff.patch import Patcher


def patch_tree(actions, tree, nsmap=None):
    patcher = MyPatcher()
    return patcher.patch(actions, tree, nsmap=nsmap)


class MyPatcher(Patcher):

    def patch(self, actions, tree, nsmap=None):
        if isinstance(tree, etree._ElementTree):
            tree = tree.getroot()
        if nsmap is not None:
            # Save the namespace:
            self._nsmap = nsmap
        else:
            self._nsmap = tree.nsmap

        # Copy the tree so we don't modify the original
        result = deepcopy(tree)

        for action in actions:
            self.handle_action(action, result)

        return result
