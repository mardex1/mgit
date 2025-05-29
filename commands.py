import time
import shutil
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

    filepath = working_dir + "/.git/logs/HEAD"  
    if not os.path.exists(filepath):
        parent = "0"*40
        initial_flag = (" (initial)")
    else:
        # get last commit on refs/heads/main
        with open(working_dir + "/.git/refs/heads/main", "r") as f:
            parent = f.read()
        initial_flag = ""

    # CHANGE!! going to set values manually, of the author, commiter and timestamp
    commit_info = "tree " + tree_hash + "\n"
    if initial_flag == "":
        commit_info += f"parent {parent}\n"
    commit_info += f"author Mardem <mardemcastro123@gmail.com> {current_time} -0300\n"
    commit_info += f"commiter Mardem <mardemcastro123@gmail.com> {current_time} -0300\n\n"
    commit_info += commit_msg

    commit_hash = create_hash_string(commit_info)

    log_commit_msg = parent + " " + commit_hash
    log_commit_msg += f" Mardem <mardemcastro123@gmail.com> {current_time} -0300 "
    log_commit_msg += f"commit{initial_flag}: {commit_msg}\n"


    # Writing new commit
    with open(working_dir + "/.git/refs/heads/main", "w") as f:
        f.write(commit_hash)

    # Logging it
    with open(working_dir + "/.git/logs/HEAD", "a") as f:
        f.write(log_commit_msg)
    with open(working_dir + "/.git/logs/refs/heads/main", "a") as f:
        f.write(log_commit_msg)

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


def git_log():
    # i need every commit hash, name and email of the author, timestamp
    # in UNIX (convert to normal time, Day of the week - month - day - hour:min:sec - year)
    # -0300 and the message

    # Searching for the git dir
    working_dir = find_git_dir()
    if working_dir == None:
        print(".git directory not found")
        return None
    
    with open(working_dir + "/.git/refs/heads/main", "r") as f:
        commit_hash = f.read()

    log_string = ""
    is_first = True
    while(True):
        last_commit_info = read_hash(working_dir + "/.git/objects/" + commit_hash) 

        lci_list = last_commit_info.split("\n")
        author_date_info = lci_list[2]
        msg = lci_list[-1]

        log_string += format_log(commit_hash, author_date_info, msg, is_first)
        is_first = False
        # This means we reached the first commit
        if len(lci_list) < 6:
            break
        else:
            commit_hash = lci_list[1].split(" ")[-1]

    return log_string


def format_log(commit_hash, author_date_info, msg, is_first):
    date = author_date_info.split(" ")[-2:]
    author = author_date_info.split(" ")[1:-2]

    readable_time = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(int(date[0])))
    time_zone = date[1]

    if is_first:
        commit_line = f"\033[33mcommit {commit_hash} (\033[1;36mHEAD\033[0m \033[33m->\033[0m \033[1;32mmain\033[0m\033[33m)\033[0m\n"
    else:
        commit_line = f"\033[33mcommit {commit_hash}\033[0m\n"
    author_line = f"Author:\t{' '.join(author)}\n"
    date_line = f"Date:\t{readable_time} {time_zone}\n"
    msg_line = f"\n\t{msg}\n"

    full_text = commit_line + author_line + date_line + msg_line

    return full_text

def git_checkout_c(commit, working_dir):

    # Checking if commit exists
    log_string = git_log()    
    if commit in log_string:
        print("Commit found!")
    else:
        print("Commit doesn't exist, failed")
        return None

    # Checking if the commit i wanna checkout to is the commit im on
    with open(working_dir + "/.git/HEAD", "r") as f:
        head = f.read()

    if head == commit:
        msg = log_string.split("\n\t")[-1]
        print(f"HEAD is now at {commit} {msg}")
        return

    clear_directory(working_dir)

    # From the commit that i want to checkout to, i wanna build the working dir
    commit_info = read_hash(working_dir + "/.git/objects/" + commit)
    tree_hash = commit_info.split("\n")[0].split(" ")[-1]
    tree_info = read_hash(working_dir + "/.git/objects/" + tree_hash)

    reconstruct_dir(tree_info, working_dir)

    with open(working_dir + "/.git/HEAD", "w") as f:
        f.write(commit)

def git_checkout_b(branch, working_dir):
    # Checking if branch exists
    path_refs = os.path.join(working_dir, ".git/", "refs/heads/")
    commit_info = None
    for filepath in os.listdir(path_refs):
        if branch == filepath:
            with open(os.path.join(path_refs, branch), "r") as f:
                branch_latest_c = f.read()
            commit_path = os.path.join(working_dir, ".git/objects/" + branch_latest_c)

            clear_directory(working_dir)

            commit_info = read_hash(commit_path)
            tree_hash = commit_info.split("\n")[0].split(" ")[-1]
            tree_info = read_hash(working_dir + "/.git/objects/" + tree_hash)

            reconstruct_dir(tree_info, working_dir)

            with open(working_dir + "/.git/HEAD", "w") as f:
                f.write("ref: refs/heads/" + branch)


def reconstruct_dir(tree_info, working_dir, current_dir=None):
    for obj in tree_info.split("\n"):
        obj_splitted = obj.split(" ")
        if obj_splitted[1] == "blob":
            blob_hash = obj_splitted[2]
            blob_name = obj_splitted[3]
            blob_content = read_hash(working_dir + "/.git/objects/" + blob_hash)
            
            if current_dir == None:
                current_dir = working_dir

            with open(current_dir + "/" + blob_name, "w") as f:
                f.write(blob_content)
        if obj_splitted[1] == "tree":
            tree_hash = obj_splitted[2]
            tree_name = obj_splitted[3] 
            new_working_dir = os.path.join(working_dir, tree_name)
            os.mkdir(new_working_dir)
            new_tree_info = read_hash(working_dir + "/.git/objects/" + tree_hash)
            reconstruct_dir(new_tree_info, working_dir, new_working_dir)


def clear_directory(dir_path):
    for item in os.listdir(dir_path):
        if item == ".git":
            continue
        file_path = os.path.join(dir_path, item)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}, {e}")
