import binascii
import zlib
import os
import graphviz

repository = input('repository path: ')


def read_git_object(git_file: str):
    global repository

    folder = git_file[:2]
    name = git_file[2:]

    filename = f"{repository}/.git/objects/{folder}/{name}"

    with open(filename, "rb") as file:
        raw_data = file.read()
    data = zlib.decompress(raw_data)

    _type, contents = data.split(b'\x00', maxsplit=1)[0:2]
    _type = _type.decode().split()[0]
    _contents = None
    if _type in ["blob", "commit"]:
        _contents = contents.decode()
    elif _type == "tree":
        _contents = list()
        while contents != b'':
            filemode, contents = contents.split(b' ', maxsplit=1)
            filename, contents = contents.split(b'\x00', maxsplit=1)
            sha1, contents = contents[:20], contents[20:]
            filemode = filemode.decode()
            filename = filename.decode()
            sha1 = binascii.hexlify(sha1).decode()
            _contents.append((filemode, filename, sha1))
    return _type, _contents


def read_heads(heads_name: str):
    global repository
    filename = f"{repository}/.git/refs/heads/{heads_name}"

    with open(filename, "rb") as file:
        data = file.read()
    contents = data.split(b'\x00', maxsplit=1)[0].decode()

    return contents


dot = graphviz.Digraph("git rep")
branch = 'master'
if os.path.exists(repository):
    last_commit = read_heads(branch)[:-1]
    content = read_git_object(last_commit)

    tree = None
    tree_short_name = "empty"
    parent_name = content[1].split('\n')[-2]
    parent_commit = None

    while content[0] == 'commit':
        content_split = content[1].split(maxsplit=4)


        if parent_commit:
            dot.node(content[1].split('\n')[-2] + '\n' + parent_commit[:6], fillcolor='orange', style='filled')
            dot.edge(parent_commit_name + '\n' + last_commit[:6], content[1].split('\n')[-2] + '\n' + parent_commit[:6])
            parent_name = content[1].split('\n')[-2]
            last_commit = parent_commit
        else:
            dot.node(content[1].split('\n')[-2] + '\n' + last_commit[:6], fillcolor='orange', style='filled')


        if content_split[0] == 'tree':
            tree = read_git_object(content_split[1])
            tree_short_name = content_split[1][:6]

        parent_commit = None
        if content_split[2] == 'parent':
            parent_commit = content_split[3]
            parent_commit_name = content[1].split('\n')[-2]

        has_next_tree = True
        while has_next_tree:
            dot.node('Tree ' + tree_short_name, fillcolor='green', style='filled')
            dot.edge(parent_name + '\n' + last_commit[:6], 'Tree ' + tree_short_name)

            next_tree = None
            has_next_tree = False
            for child in tree[1]:
                if child[0] == '40000':
                    next_tree = read_git_object(child[2])
                    next_tree_short_name = child[2][:6]
                    has_next_tree = True
                elif child[0] == '100644':
                    dot.node(child[1] + '\n' + child[2][:6], fillcolor='blue', style='filled')
                    dot.edge('Tree ' + tree_short_name, child[1] + '\n' + child[2][:6])
            if has_next_tree:
                tree = next_tree
                parent_name = 'Tree ' + tree_short_name
                tree_short_name = next_tree_short_name


        if parent_commit:
            content = read_git_object(parent_commit)
        else:
            content = "empty"
else:
    print("Repository doesn't exist")

with open("graph.dot", 'w') as f:
    f.write(dot.source)

