#!/usr/bin/env python
import os
import sys
import tkinter as tk
from tkinter import ttk
import fileinput


def search_text(tree: ttk.Treeview, query: str, item: str, found: set):
    children = tree.get_children(item)
    for child in children:
        text = tree.item(child, "text")
        if query in text.lower():
            found.add(child)
        search_text(tree, query, item=child, found=found)


def add_parent(tree: ttk.Treeview, item, add_to: set):
    p = tree.parent(item)
    if p == "":
        return
    add_to.add(p)
    add_parent(tree, p, add_to)


def add_children(tree: ttk.Treeview, item, parent_index: str, add_to: dict):
    add_to[item] = parent_index
    p = tree.get_children(item)
    if p == "":
        return
    for kid in p:
        add_children(tree, kid, parent_index=item, add_to=add_to)


def split_all(path):
    all_parts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            all_parts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            all_parts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            all_parts.insert(0, parts[1])
    return all_parts


def prepare_input(filename):
    """

    :param filename: Any
    :return: dict

    $ cat test

    /1/2/3.conf

    >>> prepare_input(test)
    {"/": {"1": {"2": {"3.conf":{}}}}}
    """
    d = {}
    for line in fileinput.input(filename):
        split = split_all(line)
        n = d
        for item in split:
            n = n.setdefault(item, {})
    return d


class TreeViewWithFilter(tk.Tk):
    def __init__(self, args):
        super().__init__()

        filename = " ".join(args)
        if len(args) == 0:
            filename = "/dev/stdin"

        self.title("Hierarchy View - {}".format(filename))
        self.geometry("800x600")
        self.rowconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=100)

        tree = ttk.Treeview(self)
        tree.heading("#0", text=filename, anchor=tk.W)
        tree.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(tree, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        self.tree = tree
        self._to_search = tk.StringVar()
        self._set_search_entry()
        d = prepare_input(args)
        for k, v in d.items():
            self.to_tree(k, v)

        for item in self.tree.get_children():
            add_children(self.tree, item, parent_index=item, add_to=self._all)

    def _set_search_entry(self):
        label = ttk.Label(self, text="Search:")
        label.grid(row=0, column=0)
        ent = ttk.Entry(self, textvariable=self._to_search)
        ent.grid(row=0, column=1, sticky=tk.W + tk.E)
        # TODO buffer keystroke events and search after a small delay
        ent.bind("<KeyRelease>", self._search)
        return ent

    def to_tree(self, name: str, values: dict, parent_index: str = ""):
        """

        :param name: node name
        :param values: dict of children
        :param parent_index: node will be appended to this node
        :return:

        >>>to_tree('root', {"a": {"s": {"d": {}}}})

        └── root
            └── a
                └── s
                    └── d
        """
        new_id = self.tree.insert(parent_index, 0, text=name)
        if len(values) == 0:
            return
        for k, v in values.items():
            self.to_tree(k, v, new_id)

    _show = set()
    _all = dict()

    def _search(self, event):
        index = -1
        for item, parent in self._all.items():
            index = index + 1
            if item == parent:
                self.tree.reattach(item, parent="", index=index)
            else:
                self.tree.reattach(item, parent=parent, index=index)

        self._show = set()

        found = set()
        query = self._to_search.get().lower()
        search_text(self.tree, query, "", found)
        for item in found:
            self._show.add(item)
            add_parent(self.tree, item, self._show)

        for item in self._all:
            if item not in self._show:
                self.tree.detach(item)

        if len(self._show) == 0:
            return

        for item in self._show:
            if len(query) == 0:
                self.tree.item(item, open=False)
            else:
                self.tree.see(item)

        self.tree.yview_moveto(0)


if __name__ == "__main__":
    t = TreeViewWithFilter(sys.argv[1:])
    t.mainloop()
