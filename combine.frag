#version 460
uniform int width;
uniform int height;
uniform int maxDepth;

struct Fragment {
    uint next;
    vec4 color;
    float depth;
};

layout(std430, binding=1) coherent buffer head {
    uint tail[];
};

layout(std430, binding=2) coherent buffer list {
    Fragment fragments[];
};

in vec2 f_uv;
out vec3 o_color;

uniform int show_scene;

uniform sampler2D scene_color;

void main() {
    // Create a list of empty fragments
    Fragment sorted_list[8] = Fragment[](
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0),
        Fragment(0, vec4(0.0), 0.0)
    );

    bool sorted_valid[8] = bool[](
        false, false, false, false,
        false, false, false, false
    );

    // calculate indexes
    uint x_index = uint(gl_FragCoord.x);
    uint y_index = uint(gl_FragCoord.y);
    uint head_index = y_index * width + x_index;
    uint list_index = tail[head_index];

    uint sorted_index = 0;
    uint count = maxDepth;
    uint current_index = list_index;

    // Insert fragments into sorted_list
    for (uint i = 0; i < 7; i++) {
        if (current_index == 0) break;

        sorted_list[sorted_index] = fragments[current_index];
        sorted_valid[sorted_index] = true;
        current_index = fragments[current_index].next;
        sorted_index++;
    }

    // Bubble sort fragments from farthest to closest
    current_index = list_index;
    Fragment temp;
    bool all_sorted = false;
    for (uint i = 0; i < count; i++) {
        all_sorted = true;
        for (uint j = 0; j < 7; j++) {
            if (!sorted_valid[j]) break;

            if (sorted_list[j].depth < sorted_list[j+1].depth) {
                temp = sorted_list[j];
                sorted_list[j] = sorted_list[j+1];
                sorted_list[j+1] = temp;

                all_sorted = false;
            }
        }

        if (all_sorted) break;
    }

    current_index = list_index;
    vec3 frag = vec3(0.0);

    // Adds the non-transparent pass to the list of fragments
    if (show_scene != 0)
        frag = texture(scene_color, f_uv).rgb;

    // Combine fragments
    for (uint i = 0; i < count; i++) {
        if (!sorted_valid[i]) break;

        frag = 
            sorted_list[i].color.rgb * sorted_list[i].color.a +
            (1.0 - sorted_list[i].color.a) * frag
        ;
    }
    
    o_color = frag;
}
