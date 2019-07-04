# Elv

This is [elv](https://github.com/RustemB/elv) implementation in python.
Elv is simple archiving program, that archives files without timestamps, access permissions, saving only file names and their content.

## Usage

```elv [alx] <Archive_name.elv> [FILE...]```


*   Pack current directory into archive.elv
```
elv a archive.elv .
```

*   List files in archive.elv (Dirs not listed, only full paths of files)

```
elv l archive.elv
```

*   Extract files into current dir

```
elv x archive.elv
```
