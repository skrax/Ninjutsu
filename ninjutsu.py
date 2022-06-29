import glob
import os
import sys

import ninja


def escape_path(word):
    return word.replace('$ ', '$$ ').replace(' ', '$ ').replace(':', '$:')


class Ninjutsu(ninja.Writer):
    def __init__(self):
        super().__init__(open("build.ninja", "w"))
        self.__init_build_dir()
        self.__add_header()
        self.__add_rules()

    def __del__(self):
        self.close()

    def __init_build_dir(self):
        self.build_dir = os.path.join(os.getcwd(), "build")
        if not os.path.exists(self.build_dir):
            os.mkdir(self.build_dir)

        assert (os.path.isdir(self.build_dir))

    def __add_header(self):
        self.comment("** AUTOGENERATED **")
        self.newline()

    def __add_rules(self):
        self.rules_dir = os.path.join(os.path.dirname(__file__), "rules")
        assert(os.path.exists(self.rules_dir) and os.path.isdir(self.rules_dir))

        [self.include(escape_path(os.path.join(self.rules_dir, rule))) for rule in
         glob.iglob("**/*.ninja", root_dir=self.rules_dir, recursive=True)]

    def glob_sources(self, source_path, extension_name, recurse=False):
        predicate = "**/*." if recurse else "*."
        root_dir = os.path.join(os.getcwd(), *source_path.split('/'))
        glob_it = glob.iglob(predicate + extension_name,
                             root_dir=root_dir,
                             recursive=recurse)

        for x in glob_it:
            s = os.path.join(root_dir, x)
            base_name, _ = os.path.splitext(x)
            o = self.make_obj_name(base_name)
            yield s, o

    def make_objs(self, source_path, extension_name, recurse=False, flags=[]):
        objs = []
        obj_vars = {}
        if any(flags):
            obj_vars["flags"] = flags

        for src, obj in self.glob_sources(source_path, extension_name, recurse):
            self.build(obj, extension_name, src, variables=obj_vars)
            objs.append(obj)
        return objs

    def as_target(self, target_t, name, objs, depends_on=[], flags=[]):
        target = ''
        inputs = objs
        implicits = []
        dylibs = []
        target_vars = {}

        match target_t:
            case 'exe':
                target = self.make_exe_name(name)
            case 'dylib':
                target = self.make_dylib_name(name)
            case 'lib':
                target = self.make_lib_name(name)
            case _:
                assert "unexpected target type"

        for dependency in depends_on:
            match dependency["target_t"]:
                case 'dylib':
                    implicits.append(dependency["target"])
                    dylibs.append(dependency["name"])
                case 'lib':
                    inputs.append(dependency["target"])
                case _:
                    assert "unexpected target type"

        if any(dylibs):
            flags = flags + ["-l" + dylib for dylib in dylibs]
            flags.append("-L./build/bin")

        if any(flags):
            target_vars["flags"] = flags

        self.build(target, target_t, inputs, implicit=implicits, variables=target_vars)

        return {"target_t": target_t, "target": target, "name": name}

    def make_obj_name(self, name):
        return os.path.join(self.build_dir, "obj", name + ".o")

    def make_exe_name(self, name):
        match sys.platform:
            case 'win32':
                return os.path.join(self.build_dir, "bin", name + ".exe")
            case 'cygwin':
                return os.path.join(self.build_dir, "bin", name + ".exe")
            case _:
                return os.path.join(self.build_dir, "bin", name)

    def make_dylib_name(self, name):
        match sys.platform:
            case 'win32':
                return os.path.join(self.build_dir, "bin", name + ".dll")
            case 'cygwin':
                return os.path.join(self.build_dir, "bin", name + ".dll")
            case 'darwin':
                return os.path.join(self.build_dir, "bin", name + ".dylib")
            case _:
                return os.path.join(self.build_dir, "bin", name + ".so")

    def make_lib_name(self, name):
        match sys.platform:
            case 'win32':
                return os.path.join(self.build_dir, "bin", name + ".lib")
            case 'cygwin':
                return os.path.join(self.build_dir, "bin", name + ".lib")
            case _:
                return os.path.join(self.build_dir, "bin", name + ".a")
