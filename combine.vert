#version 460 core

layout (location = 0) in vec2 i_pos;
layout (location = 1) in vec2 i_uv;

out vec2 f_uv;

void main() {
    // This only renders the fullscreen quad
    gl_Position = vec4(i_pos.xy, 0.5, 1.0);

    f_uv = i_uv;
}
