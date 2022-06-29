# Ninjutsu
Ninjutsu is a small Ninja build generator for Clang based projects

## Usage
```python
from Ninjutsu.ninjutsu import Ninjutsu

ninjitsu = Ninjutsu() #extends ninja.Writer

# Compile all source files in a directory
compiler_flags = ["-Wall -Werror"]

app_objs = ninjitsu.make_objs(source_path="src", extension_name="cc", flags=compiler_flags)
my_lib_objs = ninjitsu.make_objs(source_path="src/Core", extension_name="cc", flags=compiler_flags, recurse=True)

# Create targets
my_dynamic_lib = ninjitsu.as_target(target_t="dylib", name="MyLib", objs=my_lib_objs)

app = ninjitsu.as_target(target_t="exe", name="App", objs=app_objs,
                         depends_on=[my_dynamic_lib])
```
| target_t | Description     |
|----------|-----------------|
| exe      | Executable      |
| dylib    | Dynamic Library |
| lib      | Static Library  |


## Generated files and directories
```
./build.ninja <- Generated ninja file

./build/ <- Build output goes here

./build/bin <- Targets go here

./build/obj <- Object files go here
```