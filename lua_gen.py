def tab(x): return '\n'.join(['\t'+i for i in x.split('\n')])


def _handlearg(args):
    out = ''
    for i in args:
        out += str(i)+', '
    return out[:-2]


def if_stmt(ifb, elseifb=[], elseb=[]):
    # MAIN IF STMT      -  ELSE IFS  1                 2            ELSE
    # [eq(1, 2), [BODY]], [[eq(1, 3), [BODY]], [eq(1, 4), [BODY]], [BODY]]
    out = f"if {ifb[0]} then\n{tab(''.join(ifb[1])).rstrip()}\n"
    for elseif in elseifb:
        out += f"elseif {elseif[0]} then\n{tab(''.join(elseif[1])).rstrip()}\n"
    if elseb:
        out += f"else\n{tab(''.join(elseb)).rstrip()}\n"
    out += 'end\n'
    return out


def table(items):
    nl = "\n" if len(items) > 0 else ""
    return f'{{ {nl}' + ',\n'.join(items) + '}'


def return_stmt(val):
    return f"return {val}\n"


def for_range(var, start, stop, step, body):
    return f"for {var} = {start}, {stop}, {step} do\n\n{tab(''.join(body)).rstrip()}\nend\n"


def for_loop(vars, i, body):
    return f"for {', '.join(vars)} in {i} do\n{tab(''.join(body)).rstrip()}\nend\n"


def convert_dicttable(dct):
    result = '{\n'
    for name, value in dct.items():
        if isinstance(name, str):
            result += f"    [\"{name}\"] = {value},\n"
        elif isinstance(name, dict):
            result += f"    [\"{name}\"] = {convert_dicttable(value)},\n"
        else:
            result += f"    {name} = {convert_dicttable(value)}, \n"

    return result[:-2]+'\n}'


def while_stmt(cond, body):
    return f"while {cond} do\n{tab(''.join(body)).rstrip()}\nend\n"

def require(name, asname=None):
    return vardef(name if asname == None else asname, call('require', [f'"{name}"']))

def call(name, args):
    return f"{name}({_handlearg(args)})\n"


def class_def(name, methods):
    return f"""local {name} = {{}}
{method(name, 'new', ['x'], [
    vardef('_x', orop('x', table([]))),
    call('setmetatable', ['_x', 'self']),
    varset('self.__index', 'self'),
    return_stmt('_x')
])}
{''.join(methods)}"""


def method(cname, name, args, body):
    return f"function {cname}:{name}({_handlearg(args)})\n{tab(''.join(body)).rstrip()}\nend\n"


def selfcall(object, attachment, args):
    return f"{object}:{attachment}({_handlearg(args)})\n"


def vardef(name, value):
    return f"{'local ' if name[0] == '_' else ''}{name} = {value}\n"


def varset(name, value):
    return f"{name} = {value}\n"


def function(name, args, body):
    return f"local {name}\n{name} = function({_handlearg(args)})\n{tab(''.join(body)).rstrip()}\nend\n"


def eq(x, y):
    return f'{x} == {y}'


def neq(x, y):
    return f'{x} ~= {y}'


def less(x, y):
    return f'{x} < {y}'


def lesseq(x, y):
    return f'{x} <= {y}'


def greater(x, y):
    return f'{x} < {y}'


def greatereq(x, y):
    return f'{x} <= {y}'


def andop(x, y):
    return f'{x} and {y}'


def orop(x, y):
    return f'{x} or {y}'


def notop(x, y):
    return f'{x} not {y}'


def add(x, y):
    return f'{x} + {y}'


def sub(x, y):
    return f'{x} - {y}'


def mul(x, y):
    return f'{x} * {y}'


def div(x, y):
    return f'{x} / {y}'


def mod(x, y):
    return f'{x} % {y}'


def concat(x, y):
    return f'{x} .. {y}'


def lualen(s):
    return f'#{s}'


def access_index(name, ind):
    return f'{name}[{ind}]'


pythonlua_types = {
    int: 'number',
    float: 'number',
    str: 'string',
    bool: 'boolean',
    list: 'table',
    tuple: 'table',
    None: 'nil'
}


def convert_type(value):
    if value in pythonlua_types:
        return pythonlua_types[value]
    print(f"error: {value} type could not be converted")


class LuaFile:
    def __init__(self, name):
        self.name = name
        self.program = ''

    def append(self, value):
        self.program += value + '\n'

    def write(self):
        with open(self.name, 'w') as f:
            f.write(self.program)
   