def bf(c):
    # filter code
    _code = c.gsub("[^%+%-%[%]<>,%.]", "")
    _cmds = {
        '+': 'cells[ptr] = cells[ptr] + 1',
        '-': 'cells[ptr] = cells[ptr] - 1',
        '>': 'ptr = ptr + 1',
        '<': 'ptr = ptr - 1',
        '[': 'while cells[ptr] ~= 0 do',
        ']': 'end',
        ',': 'cells[ptr] = io.read(1):byte()',
        '.': 'io.write(string.char(cells[ptr]))' 
    }
    _out = 'local cells = {}\nlocal ptr = 1\nfor i = 0, 30000 do table.insert(cells, 0) end\n'
    for i in range(0, len(_code)):
        _c = _code[i]
        for cmd in _cmds:
            if _c == cmd:
                _out += _cmds[cmd] + '\n'
    _fn = __lua__("assert(loadstring(_out))")
    _fn()
bf("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++.")