#version 460 core

in vec3 f_pos;
in vec3 f_norm;

layout (location = 0) out vec4 color;
layout (location = 1) out float pos_z;

struct PointLight {
    vec3 position;
    vec3 color;
    float strength;
    float ambienceStrength;
};

uniform PointLight lights[4];
uniform int lightCount;

void main() {
    // Calculates lighting for the non-transparent pass
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

    // Stores color and z position
    color = vec4(total_color.rgb, 1.0);
    pos_z = f_pos.z;
}
