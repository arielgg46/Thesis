import os

def build_tree(paths):
    tree = {}
    for path in paths:
        parts = path.strip().split('/')
        current = tree
        for part in parts:
            current = current.setdefault(part, {})
    return tree

def print_tree(d, prefix=''):
    for i, (key, subtree) in enumerate(sorted(d.items())):
        connector = "|---- " if i == len(d) - 1 else '|---- '
        _key = ""
        for c in key:
            if c == '_':
                _key += '\\'
            _key += c
        print(f"\\texttt{'{' + prefix + connector + _key + '}'}")
        print()
        if subtree:
            extension = '    ' if i == len(d) - 1 else '|   '
            print_tree(subtree, prefix + extension)

if __name__ == '__main__':
    with open('files.txt') as f:
        paths = f.readlines()
    tree = build_tree(paths)
    print_tree(tree)
