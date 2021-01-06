#version 460 core

layout (location = 0) in vec3 i_norm;
layout (location = 1) in vec3 i_pos;

out vec3 f_pos;
out vec3 f_norm;

uniform mat4 P;
uniform mat4 M;

void main() {
    // Your standard vertex shader
    vec4 MVP_pos = P * M * vec4(i_pos.xyz * 1.0, 1.0);
    gl_Position = MVP_pos;

    f_pos = MVP_pos.xyz / MVP_pos.w;
    f_norm = i_norm;
}
