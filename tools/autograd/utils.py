import re
import os
import yaml
from .nested_dict import nested_dict


__all__ = [
    'CodeTemplate', 'IDENT_REGEX', 'YamlLoader', 'nested_dict',
    'split_name_params', 'write',
]

from tools.codegen.code_template import CodeTemplate

# You should use these lines, rather than doing it manually.
# Especially if you see this error!
#
#     File "/usr/local/lib/python2.7/dist-packages/yaml/__init__.py", line 69, in load
#       loader = Loader(stream)
#     TypeError: 'module' object is not callable
try:
    # use faster C loader if available
    from yaml import CLoader as YamlLoader
except ImportError:
    from yaml import Loader as YamlLoader

GENERATED_COMMENT = CodeTemplate(
    "@" + "generated from ${filename}")

# Matches "foo" in "foo, bar" but not "foobar". Used to search for the
# occurrence of a parameter in the derivative formula
IDENT_REGEX = r'(^|\W){}($|\W)'


# TODO: Use a real parser here; this will get bamboozled
# by signatures that contain things like std::array<bool, 2> (note the space)
def split_name_params(prototype):
    name, overload_name, params = re.match(r'(\w+)(\.\w+)?\((.*)\)', prototype).groups()
    return name, params.split(', ')


# When tracing, we record inplace operations as out-of-place operations,
# because we don't have a story for side effects in the IR yet.
#
# Doing this un-inplacing is a little delicate however; __and__ is NOT inplace!
# TODO: Do something more robust
def uninplace_api_name(api_name):
    if api_name.endswith('_') and not api_name.endswith('__'):
        api_name = api_name[:-1]
    if api_name.endswith('_out'):
        api_name = api_name[:-4]
    return api_name


def write(dirname, name, template, env):
    env['generated_comment'] = GENERATED_COMMENT.substitute(filename=template.filename)
    path = os.path.join(dirname, name)
    # See Note [Unchanging results for ninja]
    try:
        with open(path, 'r') as f:
            old_val = f.read()
    except IOError:
        old_val = None
    new_val = template.substitute(env)
    if old_val != new_val:
        with open(path, 'w') as f:
            print("Writing {}".format(path))
            f.write(new_val)
    else:
        print("Skipped writing {}".format(path))

def is_tensor_method(declaration):
    return 'Tensor' in declaration['method_of']

def is_out_variant(decl):
    return decl['name'].endswith('_out')

def op_name_with_overload(decl):
    return decl['operator_name_with_overload']

def load_op_list_and_strip_overload(op_list, op_list_path):
    if op_list is None and op_list_path is None:
        return None
    if op_list is None:
        op_list = []
    if op_list_path is not None:
        with open(op_list_path, 'r') as f:
            op_list += yaml.load(f, Loader=YamlLoader)
    # strip out the overload part
    return {opname.split('.', 1)[0] for opname in op_list}
