#version 460
uniform int width;
uniform int height;
uniform int maxDepth;

struct Fragment {
    uint next;
    vec4 color;
    float depth;
};

uniform layout(binding=0) atomic_uint counter;

// These two buffers are shared with combine.frag
layout(std430, binding=1) coherent buffer head {
    uint tail[];
};

layout(std430, binding=2) coherent buffer list {
    Fragment fragments[];
};

in vec3 f_pos;
in vec3 f_norm;

struct PointLight {
    vec3 position;
    vec3 color;
    float strength;
    float ambienceStrength;
};

uniform PointLight lights[4];
uniform int lightCount;
uniform float alpha;

uniform sampler2D scene_depth;

vec3 doLighting() {
    // Does the same lighting calculations as in shader.frag
    vec3 total_color = vec3(0.0);
    vec3 object_color = abs(f_norm);

    for (int i = 0; i < lightCount; i++) {
        vec3 ambient = lights[i].ambienceStrength * lights[i].color;

        vec3 norm = normalize(f_norm);
        vec3 lightDir = normalize(lights[i].position - f_pos);

        float diff = max(dot(norm, lightDir), 0.0);
        vec3 diffuse = diff * lights[i].color;

        vec3 viewDir = normalize(f_pos);
        vec3 reflectDir = reflect(-lightDir, norm);

        float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
        vec3 specular = 2.0 * spec * lights[i].color;

        float lightDistance = distance(lights[i].position, f_pos);
        float intensity = lights[i].strength / pow(lightDistance, 2.0);

        total_color += (ambient + diffuse + specular) * intensity * object_color;
    }

    return total_color;
}

void main() {
    // Test our z position with the non-transparent pass. If we are closer, or the
    // fragment has not been drawn to, then we can continue. Otherwise, we discard
    // the current fragment
    vec2 uv = gl_FragCoord.xy / vec2(float(width), float(height));
    float depth = texture(scene_depth, uv).r;
    if (f_pos.z > depth && depth != 0.0) discard;

    // Get the current head index
    uint x_index = uint(gl_FragCoord.x);
    uint y_index = uint(gl_FragCoord.y);
    uint head_index = y_index * width + x_index;

    // Get the next free link in the list, and update the old head
    uint list_index = atomicCounterIncrement(counter);
    uint last_index = atomicExchange(tail[head_index], list_index);

    // Store information in the new head
    vec4 frag_color = vec4(doLighting(), alpha);
    fragments[list_index].next = last_index;
    fragments[list_index].color = frag_color;
    fragments[list_index].depth = f_pos.z;
}
