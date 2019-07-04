#!/usr/bin/python3
import sys
import os

MAGIC_NUMBER = b'elv'
BLOCK_COPY_SIZE = 16777216 # 16MiB in bytes
MEANINGFULL_MESSAGES = True

def invalid_usage():
    print("Usage:")
    print("elv [alx] <Archive_name.elv> [FILE...]")
    exit()

def int_to_u64(i):
    return (i).to_bytes(8, byteorder='little', signed=False)

def int_to_u32(i):
    return (i).to_bytes(4, byteorder='little', signed=False)

def bytes_to_int(i):
    return int.from_bytes(i, byteorder="little", signed=False)

def fname(name):
    return repr(name)[1:-1]

def ensure_file_not_exists(path):
    if os.path.exists(path):
        print("File `{}` already exists, aborting".format(fname(path)))
        exit()

def ensure_file_exists(path):
    if not os.path.exists(path):
        print("File `{}` not exists, aborting".format(fname(path)))
        exit()

def safe_file_path(path):
    # Only relative paths allowed
    if os.isabs(path):
        return False

    # No parent file insertion
    if path.startswith("../") or path.endswith("/..") or "/../" in path:
        return False

    return True

def archive_file_corrupted(name, reason):
    if MEANINGFULL_MESSAGES:
        print("`{}` is not valid .elv file".format(name))
        print(reason)
    else:
        print("Invalid file format")

#TODO mmap instead of block copy
def block_copy(from_f, to_f, amount=-1):
    if amount == -1:
        block = from_f.read(BLOCK_COPY_SIZE)
        while block:
            to_f.write(block)
            block = from_f.read(BLOCK_COPY_SIZE)
    else:
        while amount > 0:
            size = min(amount, BLOCK_COPY_SIZE)
            block = from_f.read(size)

            if len(block) < size:
                print("Something went wrong while copying...")
                print("From `{}` to `{}`".format(from_f.name, to_f.name))
                exit()
                
            to_f.write(block)
            amount -= BLOCK_COPY_SIZE

def archive(archive_name, file_list):
    if len(file_list) == 0:
        invalid_usage()

    ensure_file_not_exists(archive_name)

    i = 0
    while i < len(file_list):
        f = file_list[i]
        ensure_file_exists(f)

        if os.path.isdir(f):
            file_list.extend([os.path.relpath(os.path.normpath(os.path.join(f, n)))
                              for n in os.listdir(f)])
            file_list.remove(f)
            i -= 1
        i += 1

    with open(archive_name, "wb") as out_f:
        out_f.write(MAGIC_NUMBER)

        for archiving_file in file_list:
            print("Archiving {}...".format(fname(archiving_file)))
            with open(archiving_file, "rb") as in_f:
                size = os.path.getsize(archiving_file)
                file_name = archiving_file.encode("UTF-8")

                out_f.write(int_to_u32(len(file_name))) # name size
                out_f.write(file_name) # name in utf-8

                out_f.write(int_to_u64(size)) # content size
                block_copy(in_f, out_f) # content

def create_path(path):
    if not path:
        return
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except NotADirectoryError as e:
            print("Trying to create path: `{}`, and following error happened:".format(path))
            print(str(e))
            exit()

def extract_files(a_name):
    ensure_file_exists(a_name)

    a_size = os.path.getsize(a_name)

    with open(a_name, "rb") as f:
        magic = f.read(len(MAGIC_NUMBER))
        if magic != MAGIC_NUMBER:
            archive_file_corrupted(a_name,
                                   ("Magick number doesn't match, "
                                    "expected {}, got {}")
                                   .format(MAGIC_NUMBER, magic)
                                   )

        def read(n):
            data = f.read(n)
            if len(data) != n:
                archive_file_corrupted(a_name, "Error, reached file end too soon.")
            return data

        while True:
            if f.tell() == a_size:
                break

            name_len = bytes_to_int(read(4))
            content_size = bytes_to_int(read(8))

            if name_len == 0: archive_file_corrupted(a_name, "Got zero length file name.")
            try:
                fullpath = read(name_len).decode("UTF-8")
            except UnicodeDecodeError as e:
                archive_file_corrupted(a_name, "Error at decoding file name:\n {}".format(e))
            path, name = os.path.split(fullpath)

            if not safe_file_path(fullpath):
                print("Unsafe file path: `{}`".format(fullpath))
                f.seek(content_size, 1)
                continue

            if not file_name.startswith("//"):
                print("Extracting `{}`...".format(fname(fullpath)))
                ensure_file_not_exists(fullpath)

                create_path(path)
                with open(fullpath, "wb") as out_f:
                    block_copy(f, out_f, content_size)
            else:
                f.seek(content_size, 1)

def list_files(a_name):
    ensure_file_exists(a_name)

    a_size = os.path.getsize(a_name)

    with open(a_name, "rb") as f:
        def read(n):
            data = f.read(n)
            if len(data) != n:
                archive_file_corrupted(a_name, "Error, reached file end too soon.")
            return data

        magic = f.read(len(MAGIC_NUMBER))
        if magic != MAGIC_NUMBER:
            archive_file_corrupted(a_name, "Invalid format of the file")

        while f.tell() < a_size:
            name_len = bytes_to_int(read(4))
            if f.tell() + name_len > a_size: corrupted_file()
            if name_len == 0: archive_file_corrupted(a_name, "Got zero length file name.")

            try:
                name = read(name_len).decode("UTF-8")
            except UnicodeDecodeError as e:
                archive_file_corrupted(a_name, "Error at decoding file name:\n {}".format(e))

            content_size = bytes_to_int(read(8))

            if not name.startswith("//"):
                print(fname(name)+'\t'+str(content_size))

            if f.tell() + content_size > a_size: archive_file_corrupted()
            f.seek(content_size, 1)

def main():
    args = sys.argv

    if len(args) < 3:
        invalid_usage()

    action = args[1]
    archive_name = args[2]
    file_list = args[3:]

    if len(action) != 1:
        invalid_usage()

    if action == 'a':
        archive(archive_name, file_list)
    elif action == 'l':
        list_files(archive_name)
    elif action == 'x':
        extract_files(archive_name)

if __name__ == '__main__':
    main()
