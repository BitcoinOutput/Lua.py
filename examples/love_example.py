import lualib.love

def load():
    x = 0
    y = 0
    vel = 1

def update():
    if keyboard.isDown("w"): y -= 1
    if keyboard.isDown("s"): y += 1

    if keyboard.isDown("a"): x -= 1
    if keyboard.isDown("d"): x += 1
    
def draw():
    graphics.rectangle("fill", x, y, 10, 10)

love.load = load
love.update = update
love.draw = draw