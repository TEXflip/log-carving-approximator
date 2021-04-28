from pyglet.gl import *
from pywavefront import visualization

rotation = 0

def show(obj, wireframe=True):
    window = pyglet.window.Window(width=1280, height=720, resizable=True)

    @window.event
    def on_resize(width, height):
        viewport_width, viewport_height = window.get_framebuffer_size()
        glViewport(0, 0, viewport_width, viewport_height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., float(width)/height, 1., 100.)
        glMatrixMode(GL_MODELVIEW)
        return True

    @window.event
    def on_draw():
        window.clear()
        glLoadIdentity()

        glTranslated(0.0, 0.0, -3.0)
        glRotatef(rotation, 0.0, 1.0, 0.0)

        visualization.draw(obj)

    def update(dt):
        global rotation
        rotation += 20.0 * dt

        if rotation > 720.0:
            rotation = 0.0

    if wireframe:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glLineWidth(2)

    pyglet.clock.schedule(update)
    pyglet.app.run()