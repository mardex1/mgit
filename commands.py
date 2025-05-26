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
        pass
    # client or server-side hook scripts search for git hooks
    os.mkdir(".git/hooks")
    # keeps a global exclude file for ignored patters
    os.mkdir(".git/info")
    # Store all contents of my database
    os.makedirs(".git/objects/pack")
    os.makedirs(".git/objects/info")
    # Pointers into commit objects in the data
    os.mkdir(".git/refs")

def create_hash_string(text):
    bytes_compressed = zlib.compress(text.encode())
    file_size = utils.string_len_bytes(text)

    full_text = text + str(file_size)

    hash_obj = hashlib.sha1(full_text.encode()).hexdigest()

    with open("objects/" + hash_obj, 'wb') as f:
        f.write(bytes_compressed)

    return hash_obj
    
def create_hash_path(file_path):
    """Given a file, this function compress it's content, and store it on
    a file with the name equivalent to content of the file concateneted with
    the file size, in bytes"""
    with open(file_path, 'r') as f:
        text = f.read()
    bytes_compressed = zlib.compress(text.encode())
    file_size = os.path.getsize(file_path)
    
    full_text = text + str(file_size)

    hash_obj = hashlib.sha1(full_text.encode()).hexdigest()

    with open("objects/" + hash_obj, 'wb') as f:
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
            
#            if type(i_cs) == str:
            #    index_content.append(("100644", i_cs.split(" ")[1], "0", name))
           # else:
            for i_c in i_cs:
                name_temp = name + "/" + i_c[-1]
                index_content.append(("100644", i_c[1], "0", name_temp))
    return index_content

def git_add(working_dir):
    index_content = get_index_content(working_dir)

    index = [] 
    for idx_line in index_content:
        index.append(' '.join(idx_line))
    index = '\n'.join(index)

    index_compressed = zlib.compress(index.encode())

    with open("index", "wb") as f:
        f.write(index_compressed)

def create_tree_obj(tree_quads):
    tree_string = ""
    for idx, tree_quad in enumerate(tree_quads):
        tree_string += ' '.join(tree_quad) 
        if idx+1 != len(tree_quads):
            tree_string += "\n"
    tree_hash = create_hash_string(tree_string)

    return tree_hash


def git_commit(working_dir):
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
    index_string = read_hash("index")
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

