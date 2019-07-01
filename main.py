#!/usr/bin/python3
import sys
import os

MAGIC_NUMBER = b'elv'
BLOCK_COPY_SIZE = 16777216 # 16MiB in bytes

def invalid_usage():
    print("Usage:")
    print("elv [alx] <Archive_name.elv> [FILE...]")
    exit()


def int_as_u64(i):
    return (i).to_bytes(8, byteorder='little', signed=False)

def int_as_u32(i):
    return (i).to_bytes(4, byteorder='little', signed=False)

def bytes_as_int(i):
    return int.from_bytes(i, byteorder="little", signed=False)

def fname(name):
    return repr(name)[1:-1]

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
            if len(block) != size:
                print("Corrupted file")
                exit()
            to_f.write(block)
            amount -= BLOCK_COPY_SIZE

def archive(archive_name, file_list):
    if len(file_list) == 0:
        invalid_usage()

    if os.path.exists(archive_name):
        print("File `{}` already exists, aborting".format(fname(archive_name)))
        exit()

    for f in file_list:
        if not os.path.exists(f):
            print("File `{}` not exists, aborting".format(fname(f)))
            exit()
        if os.path.isdir(f):
            file_list.extend([os.path.join(f, n) for n in os.listdir(f)])
            file_list.remove(f)

    with open(archive_name, "wb") as out_f:
        out_f.write(MAGIC_NUMBER)
        for archiving_file in file_list:
            if not os.path.exists(archiving_file):
                print("File `{}` not found, aborting"
                      .format(fname(archiving_file)))
                exit()

            print("Archiving {}...".format(fname(archiving_file)))
            with open(archiving_file, "rb") as in_f:
                size = os.path.getsize(archiving_file)
                file_name = archiving_file.encode("UTF-8")

                out_f.write(int_as_u32(len(file_name))) # name size
                out_f.write(file_name) # name in utf-8

                out_f.write(int_as_u64(size)) #content size
                block_copy(in_f, out_f) #content

    print("Done")

def create_path(path):
    if not path:
        return
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except NotADirectoryError as e:
            print("{}".format(e))
            exit()

def extract_files(archive_name):
    if not os.path.exists(archive_name):
        print("File `{}` not found, aborting"
              .format(fname(archiving_archive_name)))
        exit()

    a_size = os.path.getsize(archive_name)


    with open(archive_name, "rb") as f:
        f.seek(len(MAGIC_NUMBER))

        def read(n):
            data = f.read(n)
            if len(data) != n: corrupted_file()
            return data

        while True:
            if f.tell() == a_size:
                break

            name_len = bytes_as_int(read(4))
            # if f.tell() + name_len > a_size: corrupted_file()
            if name_len == 0: corrupted_file()
            try:
                fullpath = read(name_len).decode("UTF-8")
            except UnicodeDecodeError:
                corrupted_file()
            path, name = os.path.split(fullpath)

            print("Extracting `{}`...".format(fname(fullpath)))
            if os.path.exists(name):
                print("File `{}` already exists, aborting".format(fname(fullpath)))
                exit()
            create_path(path)

            content_size = bytes_as_int(read(8))
            # if f.tell() + content_size > a_size: corrupted_file()
            data = read(content_size)
            with open(fullpath, "wb") as out_f:
                block_copy(f, out_f)

    print("Done")

def list_files(archive_name):
    if not os.path.exists(archive_name):
        print("File `{}` not found, aborting"
              .format(fname(archive_name)))
        exit()

    a_size = os.path.getsize(archive_name)

    def corrupted_file():
        print("File `{}` corrupted, aborting".format(fname(archive_name)))
        exit()

    with open(archive_name, "rb") as f:
        f.seek(len(MAGIC_NUMBER))
        def read(n):
            data = f.read(n)
            if len(data) != n: corrupted_file()
            return data

        name_len = bytes_as_int(read(4))
        if f.tell() + name_len > a_size: corrupted_file()
        if name_len == 0: corrupted_file()
        try:
            name = read(name_len).decode("UTF-8")
        except UnicodeDecodeError:
            corrupted_file()
        content_size = bytes_as_int(read(8))

        print(fname(name)+'\t'+str(content_size))

        if f.tell() + content_size > a_size: corrupted_file()
        f.seek(content_size, 1)
    print("Done")

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
