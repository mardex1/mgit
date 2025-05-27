import time
import zlib
import os
import hashlib
import utils

def git_init():
    os.mkdir(".git")
    # The description file is used only
    # by the GitWeb program, so don’t worry about it.
    with open(".git/description", "w") as f:
        f.write("Default description")
    # project-specific config options
    with open(".git/config", "w") as f:
        pass
    # Points to the branch currently ahead
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main")
    # client or server-side hook scripts search for git hooks
    os.mkdir(".git/hooks")
    # keeps a global exclude file for ignored patters
    os.mkdir(".git/info")
    # Store all contents of my database
    os.makedirs(".git/objects/pack")
    os.makedirs(".git/objects/info")
    # Pointers into commit objects in the data
    os.makedirs(".git/refs/heads")
    os.makedirs(".git/logs/refs/heads")

def create_hash_string(text):

    # Find the git dir
    working_dir = find_git_dir()
    if working_dir == None:
        print(".git directory not found")
        return None

    bytes_compressed = zlib.compress(text.encode())
    file_size = utils.string_len_bytes(text)

    full_text = text + str(file_size)

    hash_obj = hashlib.sha1(full_text.encode()).hexdigest()

    with open(working_dir + "/.git/objects/" + hash_obj, 'wb') as f:
        f.write(bytes_compressed)

    print(hash_obj)
    return hash_obj
    
def create_hash_path(file_path):
    """Given a file, this function compress it's content, and store it on
    a file with the name equivalent to content of the file concateneted with
    the file size, in bytes"""

    # Find the git dir
    working_dir = find_git_dir()
    if working_dir == None:
        print(".git directory not found")
        return None

    with open(file_path, 'r') as f:
        text = f.read()
    bytes_compressed = zlib.compress(text.encode())
    file_size = os.path.getsize(file_path)
    
    full_text = text + str(file_size)

    hash_obj = hashlib.sha1(full_text.encode()).hexdigest()

    with open(working_dir + "/.git/objects/" + hash_obj, 'wb') as f:
        f.write(bytes_compressed)
    
    return hash_obj


def read_hash(file_path):
    """Given a sha1 encrypted file_path, returns its content"""
    with open(file_path, 'rb') as f:
        bin_text = f.read()
    bytes_decompressed = zlib.decompress(bin_text)

    print(bytes_decompressed.decode())
    return bytes_decompressed.decode()


def get_tree_quads(working_dir):
    hashes = []
    for item in os.listdir(working_dir):
        # temporary
        if item == ".git":
            continue
        item = working_dir + item
        content = []
        if os.path.isdir(item):
            tree_hashes = get_tree_quads(item + "/")
            for hash_obj in tree_hashes:
                content.append(' '.join(hash_obj))
            tree_content = '\n'.join(content)
            tree_hash = create_hash_string(tree_content)
            name = item.split("/")[-1]
            object_type = "tree"
            # stands for directory
            mode = "040000" 
            hashes.append((mode, object_type, tree_hash, name))
        else:
            # is a blob
            blob_hash = create_hash_path(item)
            name = item.split("/")[-1]
            object_type = "blob"
            # maybe change in the future
            mode = "100644"
            hashes.append((mode, object_type, blob_hash, name))
    return hashes


def get_index_content(working_dir):
    index_content = []
    for item in os.listdir(working_dir):
        if item == ".git":
            continue
        item = working_dir + item

        if os.path.isfile(item):
            hash_file = create_hash_path(item)
            name = item.split("/")[-1]
            index_content.append(("100644", hash_file, "0", name))
        else:
            i_cs = get_index_content(item + "/")
            name = item.split("/")[-1]
            
            for i_c in i_cs:
                name_temp = name + "/" + i_c[-1]
                index_content.append(("100644", i_c[1], "0", name_temp))
    return index_content


def git_add():
    # Find the git dir
    working_dir = find_git_dir()
    if working_dir == None:
        print(".git directory not found")
        return None

    index_content = get_index_content(working_dir)

    index = [] 
    for idx_line in index_content:
        index.append(' '.join(idx_line))
    index = '\n'.join(index)

    index_compressed = zlib.compress(index.encode())

    with open(working_dir + "/.git/index", "wb") as f:
        f.write(index_compressed)


def create_tree_obj(tree_quads):
    tree_string = ""
    for idx, tree_quad in enumerate(tree_quads):
        tree_string += ' '.join(tree_quad) 
        if idx+1 != len(tree_quads):
            tree_string += "\n"
    tree_hash = create_hash_string(tree_string)

    return tree_hash


def git_commit(commit_msg):
    # Searching for the git dir
    working_dir = find_git_dir()
    if working_dir == None:
        print(".git directory not found")
        return None

    # First, i want to create a tree for each directory on my working dir
    hashes = []
    for item in os.listdir(working_dir):
        # Dont wanna do anything with .git dir
        if item == ".git":
            continue
        item = working_dir + item    

        # CHANGE!! check in index if one blob is present inside a tree, only than
        # create the tree
        if os.path.isdir(item):
            tree_quads = get_tree_quads(item + "/")
            # Creating the tree object
            tree_hash = create_tree_obj(tree_quads)
            name = item.split("/")[-1]
            hashes.append(("040000", "tree", tree_hash, name)) 

    # Find blob hashes on index
    index_string = read_hash(working_dir + "/.git/index")
    index_list = index_string.split("\n")
    for blob in index_list:
        blob_list = blob.split(" ")
        if "/" in blob_list[3]:
            continue
        blob_list_hash = blob_list[1]
        blob_list_perm = blob_list[0]
        blob_list_name = blob_list[3]

        hashes.append((blob_list_perm, "blob", blob_list_hash, blob_list_name))

    # Then, i want to create the commit tree
    tree_hash = create_tree_obj(hashes)
    
    # Calculate time of the commit
    current_time = str(time.time())
    for idx, num in enumerate(current_time):
        if num == ".":
            dot_idx = idx
    current_time = current_time[slice(0, dot_idx)]

    # CHANGE!! going to set values manually, of the author, commiter and timestamp
    commit_info = "tree " + tree_hash + "\n"
    commit_info += f"author Mardem <mardemcastro123@gmail.com> {current_time} -0300\n"
    commit_info += f"commiter Mardem <mardemcastro123@gmail.com> {current_time} -0300\n\n"
    commit_info += commit_msg

    commit_hash = create_hash_string(commit_info)

    filepath = working_dir + "/.git/logs/HEAD"  

    if not os.path.exists(filepath):
        parent = "0"*40
    else:
        # get last commit on refs/heads/main
        with open(working_dir + "/.git/refs/heads/main", "r") as f:
            parent = f.read()

    commit_info_split = commit_info.split("\n\n")[0]
    aditional_info = "commit (initial): {commit_msg}"
    full_text = parent + " " + commit_info_split + " " + aditional_info + "\n"

    # Writing new commit
    with open(working_dir + "/.git/refs/heads/main", "w") as f:
        f.write(commit_hash)

    # Logging it
    with open(working_dir + "/.git/logs/HEAD", "a") as f:
        f.write(full_text)
    with open(working_dir + "/.git/logs/refs/heads/main", "a") as f:
        f.write(full_text)

    return


def find_git_dir(path=None):
    if path == "":
        return None    
    elif path == None:
        current_path = os.getcwd()
    else:
        current_path = path

    for item in os.listdir(current_path):
        if item == ".git":
            return current_path + "/" 
    list_path = current_path.split("/")[:-1]
    new_path = '/'.join(list_path)
    return find_git_dir(new_path)
