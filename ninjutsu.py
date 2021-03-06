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
        assert (os.path.exists(self.rules_dir) and os.path.isdir(self.rules_dir))

        path = os.path.join(self.rules_dir, "**/*.ninja")
        [self.include(escape_path(os.path.join(self.rules_dir, rule))) for rule in glob.iglob(path, recursive=True)]

    def glob_sources(self, source_path, extension_name, out_extension_fn, recurse=False):
        predicate = "**/*." if recurse else "*."
        root_dir = os.path.join(os.getcwd(), *source_path.split('/'))
        path = os.path.join(root_dir, predicate + extension_name)
        glob_it = glob.iglob(path, recursive=recurse)

        for x in glob_it:
            s = os.path.join(root_dir, x)
            base_name, _ = os.path.splitext(os.path.basename(x))
            o = out_extension_fn(base_name)
            yield s, o

    def make_shaders(self, source_path, recurse=False):
        shaders = []
        frag_sources = self.glob_sources(source_path, "frag", self.make_frag_shader_name, recurse)
        vert_sources = self.glob_sources(source_path, "vert", self.make_vert_shader_name, recurse)

        for src, shader in frag_sources:
            self.build(shader, 'shader', src)
            shaders.append(shader)

        for src, shader in vert_sources:
            self.build(shader, 'shader', src)
            shaders.append(shader)

        return shaders

    def make_objs(self, source_path, extension_name, recurse=False, flags=[]):
        objs = []
        obj_vars = {}
        if any(flags):
            obj_vars["flags"] = flags

        for src, obj in self.glob_sources(source_path, extension_name, self.make_obj_name, recurse):
            self.build(obj, 'cc', src, variables=obj_vars)
            objs.append(obj)
        return objs

    def as_target(self, target_t, name, objs, depends_on=[], flags=[]):
        target = ''
        inputs = objs
        implicits = []
        dylibs = []
        target_vars = {}

        target_map = {
            'exe': self.make_exe_name(name),
            'dylib': self.make_dylib_name(name),
            'lib': self.make_lib_name(name)
        }

        target = target_map.get(target_t)
        assert target is not None

        for dependency in depends_on:
            dep_t = dependency["target_t"]
            if dep_t == 'dylib':
                implicits.append(dependency["target"])
                dylibs.append(dependency["name"])
            elif dep_t == 'lib':
                inputs.append(dependency["target"])
            else:
                assert "unexpected target type"

        if any(dylibs):
            flags = flags + ["-l" + dylib for dylib in dylibs]
            flags.append("-L./build/bin")

        if any(flags):
            target_vars["flags"] = flags

        self.build(target, target_t, inputs, implicit=implicits, variables=target_vars)

        return {"target_t": target_t, "target": target, "name": name}

    def make_frag_shader_name(self, name):
        return os.path.join(self.build_dir,"bin", "shaders", name + ".frag.spv")

    def make_vert_shader_name(self, name):
        return os.path.join(self.build_dir, "bin", "shaders", name + ".vert.spv")

    def make_obj_name(self, name):
        return os.path.join(self.build_dir, "obj", name + ".o")

    def make_exe_name(self, name):
        names_map = {
            'win32': os.path.join(self.build_dir, "bin", name + ".exe"),
            'cygwin': os.path.join(self.build_dir, "bin", name + ".exe"),
            'default': os.path.join(self.build_dir, "bin", name)
        }

        return names_map.get(sys.platform, names_map.get('default'))

    def make_dylib_name(self, name):
        names_map = {
            'win32': os.path.join(self.build_dir, "bin", name + ".dll"),
            'cygwin': os.path.join(self.build_dir, "bin", name + ".dll"),
            'darwin': os.path.join(self.build_dir, "bin", name + ".dylib"),
            'default': os.path.join(self.build_dir, "bin", name + ".so")
        }

        return names_map.get(sys.platform, names_map.get('default'))

    def make_lib_name(self, name):
        names_map = {
            'win32': os.path.join(self.build_dir, "bin", name + ".lib"),
            'cygwin': os.path.join(self.build_dir, "bin", name + ".lib"),
            'default': os.path.join(self.build_dir, "bin", name + ".a")
        }

        return names_map.get(sys.platform, names_map.get('default'))
