import glfw
import OpenGL.GL as GL
import ctypes
import numpy as np
import math
from OpenGL import images
images.TYPE_TO_ARRAYTYPE[GL.GL_UNSIGNED_INT_24_8] = GL.GL_UNSIGNED_INT
images.TIGHT_PACK_FORMATS[GL.GL_UNSIGNED_INT_24_8] = 4

WINDOW_RES_X = 1280
WINDOW_RES_Y = 720
SHOW_NON_TRANSPARENT = True

# Loads a .obj file. It only supports files that have only positional and
# normal data. All faces must be triangulated
class Model():
    def __init__(self, path):
        vao = GL.glGenVertexArrays(1)
        vbo = GL.glGenBuffers(1)
        veo = GL.glGenBuffers(1)

        file = open(path, "r")
        data = file.readlines()
        file.close()
    
        vert_list = []
        norm_list = []
        ind_list = {}

        vertices = []
        indices = []

        for line in data:
            if line.startswith("v "):
                parts = (line[1:]).split()
                vert_list += [[float(parts[0]), float(parts[1]), float(parts[2])]]
        
            elif line.startswith("vn "):
                parts = (line[2:]).split()
                norm_list += [[float(parts[0]), float(parts[1]), float(parts[2])]]

            elif line.startswith("f "):
                faces = (line[1:]).split()

                for face in faces:
                    if face in ind_list:
                        indices += [ind_list[face]]
                
                    else:
                        parts = face.split("/")
                        index = len(vertices) // 6
                        ind_list[face] = index
                        indices += [index]

                        vert_index = int(parts[0]) - 1 
                        norm_index = int(parts[2]) - 1

                        vertices += norm_list[norm_index]
                        vertices += vert_list[vert_index]

        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)

        GL.glBindVertexArray(vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices.data, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, veo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices.data, GL.GL_STATIC_DRAW)

        # Normal: vec3, Position: vec3
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, (3+3) * 4, ctypes.c_void_p(0))
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, (3+3) * 4, ctypes.c_void_p(3 * 4))

        self.vao = vao
        self.count = len(indices)
    
    def draw(self):
        GL.glBindVertexArray(self.vao)

        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)

        GL.glDrawElements(GL.GL_TRIANGLES, self.count, GL.GL_UNSIGNED_INT, ctypes.c_void_p(0))

# Creates an OpenGL shader program from two files
class Shader():
    def __init__(self, vert_path, frag_path):
        file = open(vert_path, "r")
        vert = file.read()
        file.close()

        file = open(frag_path, "r")
        frag = file.read()
        file.close()

        vert_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        frag_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)

        GL.glShaderSource(vert_shader, vert)
        GL.glShaderSource(frag_shader, frag)

        GL.glCompileShader(vert_shader)
        GL.glCompileShader(frag_shader)

        vert_log = GL.glGetShaderInfoLog(vert_shader)
        frag_log = GL.glGetShaderInfoLog(frag_shader)

        if vert_log:
            print("VERTEX (" + vert_path + "): " + vert_log.decode())
            quit(-1)
    
        if frag_log:
            print("FRAGMENT (" + frag_path + "): " + frag_log.decode())
            quit(-1)

        shader = GL.glCreateProgram()
        GL.glAttachShader(shader, vert_shader)
        GL.glAttachShader(shader, frag_shader)
        GL.glLinkProgram(shader)
        shader_log = GL.glGetProgramInfoLog(shader)

        if shader_log:
            print("LINK (" + vert_path + ", " + frag_path + "): " + shader_log.decode())
            quit(-1)
    
        GL.glDeleteShader(vert_shader)
        GL.glDeleteShader(frag_shader)

        self.shader = shader
        self.uniforms = {}
    
    def use(self):
        GL.glUseProgram(self.shader)
    
    def getUniform(self, name):
        if name in self.uniforms:
            return self.uniforms[name]

        uniform_location = GL.glGetUniformLocation(self.shader, name)
        self.uniforms[name] = uniform_location
        return uniform_location

    def setMatrix4(self, name, m):
        self.use()

        uniform_location = self.getUniform(name)
        if uniform_location != -1:
            GL.glUniformMatrix4fv(uniform_location, 1, GL.GL_FALSE, m.data)

    def setFloat(self, name, f):
        self.use()

        uniform_location = self.getUniform(name)
        if uniform_location != -1:
            GL.glUniform1f(uniform_location, float(f))
    
    def setFloat3(self, name, f0, f1, f2):
        self.use()

        uniform_location = self.getUniform(name)
        if uniform_location != -1:
            GL.glUniform3f(uniform_location, float(f0), float(f1), float(f2))
    
    def setTexture(self, name, texture, index, type=GL.GL_TEXTURE_2D):
        self.use()

        uniform_location = self.getUniform(name)
        if uniform_location != -1:
            GL.glActiveTexture(GL.GL_TEXTURE0 + int(index))
            GL.glBindTexture(type, texture)
            GL.glUniform1i(uniform_location, int(index))

    def setInt(self, name, i):
        self.use()

        uniform_location = self.getUniform(name)
        if uniform_location != -1:
            GL.glUniform1i(uniform_location, int(i))

if __name__ == "__main__":
    # Creates an OpenGL 4.6 window
    glfw.init()

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(WINDOW_RES_X, WINDOW_RES_Y, "OpenGL Transparency", None, None)
    print("Resolution: " + str(WINDOW_RES_X) + "x" + str(WINDOW_RES_Y))

    glfw.make_context_current(window)
    GL.glViewport(0, 0, WINDOW_RES_X, WINDOW_RES_Y)

    # Get the max size that our A-Buffer can be
    max_block_size = GL.glGetIntegerv(GL.GL_MAX_SHADER_STORAGE_BLOCK_SIZE)
    print("Max shader uniform block size:", max_block_size)

    # Calculate the sizes for the different buffers
    frag_linked_list_depth = 8
    frag_list_size = WINDOW_RES_X * WINDOW_RES_Y * (6) * 4 * frag_linked_list_depth
    frag_list_size = min(frag_list_size, max_block_size)
    frag_head_size = WINDOW_RES_X * WINDOW_RES_Y * 4
    print("Max fragments per pixel:", frag_linked_list_depth)
    print("Linked list size:", frag_list_size/1024/1024, "MB")
    print("Head size:", frag_head_size/1024/1024, "MB")
    print("A-Buffer size:", (frag_list_size + frag_head_size)/1024/1024, "MB")

    frag_flags = GL.GL_MAP_WRITE_BIT | GL.GL_MAP_PERSISTENT_BIT | GL.GL_MAP_COHERENT_BIT

    # Create the A-Buffer
    frag_head_buffer = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_SHADER_STORAGE_BUFFER, frag_head_buffer)
    GL.glBufferData(GL.GL_SHADER_STORAGE_BUFFER, frag_head_size, ctypes.c_void_p(0), GL.GL_DYNAMIC_COPY)
    GL.glBindBufferBase(GL.GL_SHADER_STORAGE_BUFFER, 1, frag_head_buffer)

    frag_list_buffer = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_SHADER_STORAGE_BUFFER, frag_list_buffer)
    GL.glBufferData(GL.GL_SHADER_STORAGE_BUFFER, frag_list_size, ctypes.c_void_p(0), GL.GL_DYNAMIC_COPY)
    GL.glBindBufferBase(GL.GL_SHADER_STORAGE_BUFFER, 2, frag_list_buffer)

    # Create the atomic counter
    reset_value = ctypes.c_int32(0)
    frag_counter = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ATOMIC_COUNTER_BUFFER, frag_counter)
    GL.glBindBufferBase(GL.GL_ATOMIC_COUNTER_BUFFER, 0, frag_counter)
    GL.glBufferStorage(GL.GL_ATOMIC_COUNTER_BUFFER, 4, ctypes.pointer(reset_value), frag_flags)

    # Create the fullscreen quad for the combine pass
    rect = GL.glGenVertexArrays(1)
    rect_vbo = GL.glGenBuffers(1)
    rect_veo = GL.glGenBuffers(1)

    # Position: vec2, UV: vec2
    rect_vertices = [
        -1.0, -1.0,  0.0, 0.0,
         1.0, -1.0,  1.0, 0.0,
        -1.0,  1.0,  0.0, 1.0,
         1.0,  1.0,  1.0, 1.0
    ]

    rect_indices = [
        2, 0, 1,
        1, 3, 2
    ]

    rect_vertices = np.array(rect_vertices, dtype=np.float32)
    rect_indices = np.array(rect_indices, dtype=np.uint32)

    rect_count = len(rect_indices)

    GL.glBindVertexArray(rect)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, rect_vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, rect_vertices.nbytes, rect_vertices.data, GL.GL_STATIC_DRAW)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, rect_veo)
    GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, rect_indices.nbytes, rect_indices.data, GL.GL_STATIC_DRAW)

    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, (2+2) * 4, ctypes.c_void_p(0))
    GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, (2+2) * 4, ctypes.c_void_p(2 * 4))

    # Create a framebuffer for the non-transparent geometry
    framebuffer = GL.glGenFramebuffers(1)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer)

    # Color texture
    framebuffer_color = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, framebuffer_color)

    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, WINDOW_RES_X, WINDOW_RES_Y, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, ctypes.c_void_p(0))

    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, framebuffer_color, 0)

    # Screen space z position
    framebuffer_z = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, framebuffer_z)

    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_R32F, WINDOW_RES_X, WINDOW_RES_Y, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, ctypes.c_void_p(0))

    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1, GL.GL_TEXTURE_2D, framebuffer_z, 0)

    # Depth and stencil buffer
    framebuffer_depth = GL.glGenRenderbuffers(1)
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, framebuffer_depth)
    GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH24_STENCIL8, WINDOW_RES_X, WINDOW_RES_Y)
    GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_STENCIL_ATTACHMENT, GL.GL_RENDERBUFFER, framebuffer_depth)

    # Perspective matrix calculations
    n = 0.05
    f = 500.0
    aspect = WINDOW_RES_X / WINDOW_RES_Y
    FOV = 70.0
    
    q = 1 / math.tan(math.radians(FOV / 2))
    a = q / aspect
    b = (f + n) / (n - f)
    c = (2 * f * n) / (n - f)

    P = np.array([
        [a, 0, 0, 0],
        [0, q, 0, 0],
        [0, 0, b, -1],
        [0, 0, c, 0]
    ], dtype=np.float32)

    # Position variables
    X = 0.0
    Y = -0.0
    Z = -4.0

    # Alpha value
    A = 0.4

    # Load models
    monkey = Model("monkey.obj")
    rings = Model("rings.obj")

    # Load shaders
    monkey_shader = Shader("shader.vert", "shader.frag")
    frag_shader = Shader("shader.vert", "transparent.frag")
    comb_shader = Shader("combine.vert", "combine.frag")

    # Upload uniform data
    frag_shader.setInt("width", WINDOW_RES_X)
    frag_shader.setInt("height", WINDOW_RES_Y)

    comb_shader.setInt("width", WINDOW_RES_X)
    comb_shader.setInt("height", WINDOW_RES_Y)

    lights = [
        [[5.0, 0.0, 0.0], [1.0, 1.0, 1.0], 30.0, 0.4],
    ]

    # Upload light uniform data
    for i in range(len(lights)):
        light = "lights[" + str(i) + "]"
        monkey_shader.setFloat3(light + ".position", *lights[i][0])
        monkey_shader.setFloat3(light + ".color", *lights[i][1])
        monkey_shader.setFloat(light + ".strength", lights[i][2])
        monkey_shader.setFloat(light + ".ambienceStrength", lights[i][3])

        frag_shader.setFloat3(light + ".position", *lights[i][0])
        frag_shader.setFloat3(light + ".color", *lights[i][1])
        frag_shader.setFloat(light + ".strength", lights[i][2])
        frag_shader.setFloat(light + ".ambienceStrength", lights[i][3])

    monkey_shader.setInt("lightCount", min(len(lights), 4))
    frag_shader.setInt("lightCount", min(len(lights), 4))

    # Upload max transparent triangles per pixel uniform
    comb_shader.setInt("maxDepth", frag_linked_list_depth)

    # Upload perspective matrix uniform
    monkey_shader.setMatrix4("P", P)
    frag_shader.setMatrix4("P", P)

    # Misc uniform
    if SHOW_NON_TRANSPARENT:
        comb_shader.setInt("show_scene", 1)
    else:
        comb_shader.setInt("show_scene", 0)

    # Delta time variables
    delta = 0
    last_time = glfw.get_time()

    while not glfw.window_should_close(window):
        # Delta time calculations
        current_time = glfw.get_time()
        delta = current_time - last_time
        last_time = current_time

        # Put buffer onto screen and update inputs
        glfw.swap_buffers(window)
        glfw.poll_events()

        # Clear the current framebuffer
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Make sure these are one
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_CULL_FACE)

        # Calculate model matrix for the non-transparent pass
        M = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0.25, 0, Z+0.5, 1]
        ], dtype=np.float32)

        # Setup framebuffers for the non-transparent pass
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer)
        buffers = [GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT1, ]
        GL.glDrawBuffers(2, buffers)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Draw the non-transparent pass
        monkey_shader.setMatrix4("M", M)
        monkey_shader.use()
        monkey.draw()

        # Calculate the model matrix fot the 
        M = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [X, Y, Z, 1]
        ], dtype=np.float32)

        # Make objects move, and transparency to vary
        X = math.cos(last_time*1.12593)
        A = (math.sin(last_time)+1.0) / 2.0

        frag_shader.setMatrix4("M", M)
        frag_shader.setFloat("alpha", A)

        # Clear the A-Buffer
        value = ctypes.c_uint8(0)
        GL.glClearNamedBufferData(frag_head_buffer, GL.GL_R8UI, GL.GL_RED_INTEGER, GL.GL_UNSIGNED_BYTE, ctypes.pointer(value))

        # Reset the atomic counter to zero
        GL.glBindBuffer(GL.GL_ATOMIC_COUNTER_BUFFER, frag_counter)
        counter_ptr = GL.glMapBufferRange(GL.GL_ATOMIC_COUNTER_BUFFER, 0, 4,
            GL.GL_MAP_WRITE_BIT | GL.GL_MAP_INVALIDATE_BUFFER_BIT | GL.GL_MAP_UNSYNCHRONIZED_BIT
        )
        
        counter_val = ctypes.cast(counter_ptr, ctypes.POINTER(ctypes.c_int))
        counter_val[0] = 0

        GL.glUnmapBuffer(GL.GL_ATOMIC_COUNTER_BUFFER)
        GL.glBindBuffer(GL.GL_ATOMIC_COUNTER_BUFFER, 0)

        # Bind the backbuffer for the next two passes
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        # Give the transparent pass the z buffer from the non-transparent
        # pass for eary z testing
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, framebuffer_z)

        frag_shader.use()

        # Disable this, just in case
        GL.glDisable(GL.GL_DEPTH_TEST)

        # Start the transparency pass. The transparency pass does not
        # actually draw anything to the screen. Instead, it populates
        # the A-Buffer with data
        monkey.draw()

        # Calculate the model matrix for the rings
        M = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [-X, Y, Z, 1]
        ], dtype=np.float32)
        frag_shader.setMatrix4("M", M)

        rings.draw()
        GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT)

        # Pass the color data from the non-transparent pass to the
        # combine pass. It still has the A-Buffer bound as well
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, framebuffer_color)

        # Draw a fullscreen quad for the combine pass
        comb_shader.use()
        GL.glBindVertexArray(rect)
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glDrawElements(GL.GL_TRIANGLES, rect_count, GL.GL_UNSIGNED_INT, ctypes.c_void_p(0))

    glfw.terminate()
