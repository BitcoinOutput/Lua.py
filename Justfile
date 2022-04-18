set shell := ["powershell", "-c"]

gen_love:
    python ./tools/genbind.py love lib/love.bnd lib/love.py