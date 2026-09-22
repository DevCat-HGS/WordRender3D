"""Programas GLSL 1.20: iluminación de bloques y agua con olas Gerstner."""
from OpenGL.GL import (
    GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS,
    glCreateShader, glShaderSource, glCompileShader, glGetShaderiv,
    glGetShaderInfoLog, glCreateProgram, glAttachShader, glBindAttribLocation,
    glLinkProgram, glGetProgramiv, glGetProgramInfoLog, glDeleteShader,
    glGetUniformLocation,
)

SOLIDO_VERT = """
#version 120
attribute vec3 a_pos;
attribute vec3 a_normal;
attribute vec3 a_color;
attribute vec2 a_aux;
varying vec3 v_normal;
varying vec3 v_color;
varying vec3 v_world;
varying float v_ao;
varying float v_tile;
void main() {
    v_world = a_pos;
    v_normal = a_normal;
    v_color = a_color;
    v_ao = a_aux.x;
    v_tile = a_aux.y;
    gl_Position = gl_ModelViewProjectionMatrix * vec4(a_pos, 1.0);
}
"""

SOLIDO_FRAG = """
#version 120
varying vec3 v_normal;
varying vec3 v_color;
varying vec3 v_world;
varying float v_ao;
varying float v_tile;
uniform vec3 u_sun_dir;
uniform vec3 u_sun_color;
uniform vec3 u_ambient;
uniform float u_sun_fuerza;
uniform vec3 u_luna_dir;
uniform float u_luna_fuerza;
uniform sampler2D u_atlas;
vec2 tile_uv(float tile, vec2 uv) {
    float tx = mod(tile, 4.0);
    float ty = floor(tile / 4.0);
    vec2 f = fract(uv);
    f = f * 0.96 + 0.02;
    return (vec2(tx, ty) + f) / 4.0;
}
void main() {
    vec3 N = normalize(v_normal);
    vec2 uv;
    vec3 an = abs(N);
    if (an.y >= an.x && an.y >= an.z) uv = v_world.xz;
    else if (an.x >= an.z) uv = v_world.zy;
    else uv = v_world.xy;
    vec4 tex = texture2D(u_atlas, tile_uv(v_tile, uv));
    if (tex.a < 0.35) discard;
    float ndl = max(dot(N, normalize(u_sun_dir)) * 0.65 + 0.35, 0.0);
    float ndm = max(dot(N, normalize(u_luna_dir)), 0.0);
    vec3 luz = u_ambient * 1.05
             + u_sun_color * ndl * (0.35 + 0.75 * u_sun_fuerza)
             + vec3(0.26, 0.32, 0.52) * ndm * u_luna_fuerza;
    vec3 col = tex.rgb * v_color * luz * clamp(v_ao, 0.4, 1.15);
    gl_FragColor = vec4(col, 1.0);
}
"""

ANIMAL_VERT = """
#version 120
attribute vec3 a_pos;
attribute vec3 a_normal;
attribute vec3 a_color;
varying vec3 v_normal;
varying vec3 v_color;
void main() {
    v_normal = a_normal;
    v_color = a_color;
    gl_Position = gl_ModelViewProjectionMatrix * vec4(a_pos, 1.0);
}
"""

ANIMAL_FRAG = """
#version 120
varying vec3 v_normal;
varying vec3 v_color;
uniform vec3 u_sun_dir;
uniform vec3 u_sun_color;
uniform vec3 u_ambient;
uniform float u_sun_fuerza;
uniform vec3 u_luna_dir;
uniform float u_luna_fuerza;
void main() {
    vec3 N = normalize(v_normal);
    float ndl = max(dot(N, normalize(u_sun_dir)) * 0.7 + 0.3, 0.0);
    float ndm = max(dot(N, normalize(u_luna_dir)), 0.0);
    vec3 luz = u_ambient * 1.1
             + u_sun_color * ndl * (0.45 + 0.7 * u_sun_fuerza)
             + vec3(0.28, 0.34, 0.55) * ndm * u_luna_fuerza;
    gl_FragColor = vec4(v_color * luz, 1.0);
}
"""

AGUA_VERT = """
#version 120
attribute vec3 a_pos;
attribute vec3 a_normal;
attribute vec3 a_color;
attribute vec2 a_aux;
uniform float u_time;
varying vec3 v_world;
varying vec3 v_normal;
varying vec3 v_color;
varying float v_depth;
varying float v_crest;
varying float v_wave;

void gerstner(inout vec3 p, inout vec3 tang, inout vec3 binm, inout float crest,
              vec2 dir, float amp, float freq, float speed, float steep) {
    dir = normalize(dir);
    float ph = freq * dot(dir, p.xz) + speed * u_time;
    float s = sin(ph);
    float c = cos(ph);
    float qa = steep * amp;
    p.x += dir.x * qa * c;
    p.z += dir.y * qa * c;
    p.y += amp * s;
    crest += s * (amp / 0.08);
    float wa = freq * amp;
    float ss = s * wa;
    float cc = c * wa;
    tang += vec3(-steep * dir.x * dir.x * ss, dir.x * cc, -steep * dir.x * dir.y * ss);
    binm += vec3(-steep * dir.x * dir.y * ss, dir.y * cc, -steep * dir.y * dir.y * ss);
}

void main() {
    vec3 p = a_pos;
    float wave = a_aux.x;
    v_depth = a_aux.y;
    v_color = a_color;
    v_wave = wave;
    float crest = 0.0;
    vec3 tang = vec3(1.0, 0.0, 0.0);
    vec3 binm = vec3(0.0, 0.0, 1.0);
    if (wave > 0.01) {
        gerstner(p, tang, binm, crest, vec2( 1.00,  0.42), 0.145, 1.25, 1.55, 0.62);
        gerstner(p, tang, binm, crest, vec2(-0.65,  1.00), 0.095, 0.95, 1.10, 0.50);
        gerstner(p, tang, binm, crest, vec2( 0.80, -0.90), 0.055, 2.15, 2.05, 0.42);
        gerstner(p, tang, binm, crest, vec2( 1.40,  1.10), 0.028, 3.20, 2.70, 0.32);
        p = mix(a_pos, p, clamp(wave, 0.0, 1.0));
        v_normal = normalize(cross(binm, tang));
        if (v_normal.y < 0.0) v_normal = -v_normal;
    } else {
        v_normal = a_normal;
    }
    v_crest = crest;
    v_world = p;
    gl_Position = gl_ModelViewProjectionMatrix * vec4(p, 1.0);
}
"""

AGUA_FRAG = """
#version 120
varying vec3 v_world;
varying vec3 v_normal;
varying vec3 v_color;
varying float v_depth;
varying float v_crest;
varying float v_wave;
uniform vec3 u_sun_dir;
uniform vec3 u_sun_color;
uniform vec3 u_ambient;
uniform vec3 u_cam_pos;
uniform float u_sun_fuerza;
uniform vec3 u_luna_dir;
uniform float u_luna_fuerza;
uniform float u_time;

void main() {
    vec3 N = normalize(v_normal);
    if (!gl_FrontFacing) N = -N;
    vec3 V = normalize(u_cam_pos - v_world);
    vec3 L = normalize(u_sun_dir);
    vec3 Lm = normalize(u_luna_dir);

    float deep = clamp(v_depth * 0.22, 0.0, 1.0);
    vec3 poco = vec3(0.14, 0.52, 0.80);
    vec3 hondo = vec3(0.04, 0.22, 0.48);
    vec3 albedo = mix(poco, hondo, deep);
    albedo = mix(v_color, albedo, 0.80);

    float cau = sin(v_world.x * 3.6 + u_time * 2.0) * sin(v_world.z * 3.1 - u_time * 1.55);
    albedo += vec3(0.08, 0.18, 0.20) * cau * (1.0 - deep) * 0.45;

    float ndl = max(dot(N, L) * 0.45 + 0.20, 0.0);
    float spec = pow(max(dot(N, normalize(L + V)), 0.0), 280.0) * u_sun_fuerza;
    float specm = pow(max(dot(N, normalize(Lm + V)), 0.0), 90.0) * u_luna_fuerza;
    float fres = pow(1.0 - max(dot(N, V), 0.0), 4.0);

    vec3 col = albedo * (u_ambient * 1.2 + u_sun_color * ndl * 0.70);
    col += u_sun_color * spec * 1.35;
    col += vec3(0.55, 0.68, 1.00) * specm * 0.55;
    col = mix(col, mix(vec3(0.10, 0.32, 0.55), u_sun_color, u_sun_fuerza * 0.45), fres * 0.35);

    float foam = smoothstep(0.15, 0.85, v_crest) * v_wave;
    col = mix(col, vec3(0.82, 0.93, 0.98), foam * 0.70);

    float alpha = mix(0.78, 0.93, deep) + fres * 0.10;
    gl_FragColor = vec4(col, clamp(alpha, 0.74, 0.96));
}
"""


def _log(msg):
    if isinstance(msg, bytes):
        return msg.decode("utf-8", "replace")
    return str(msg)


def _shader(tipo, fuente):
    sid = glCreateShader(tipo)
    glShaderSource(sid, fuente)
    glCompileShader(sid)
    if not glGetShaderiv(sid, GL_COMPILE_STATUS):
        raise RuntimeError(_log(glGetShaderInfoLog(sid)))
    return sid


def compilar(vert, frag, atributos):
    vs, fs = _shader(GL_VERTEX_SHADER, vert), _shader(GL_FRAGMENT_SHADER, frag)
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    for loc, nombre in atributos.items():
        glBindAttribLocation(prog, loc, nombre.encode("ascii"))
    glLinkProgram(prog)
    glDeleteShader(vs)
    glDeleteShader(fs)
    if not glGetProgramiv(prog, GL_LINK_STATUS):
        raise RuntimeError(_log(glGetProgramInfoLog(prog)))
    return prog


def uniforms(prog, nombres):
    return {n: glGetUniformLocation(prog, n) for n in nombres}


LOC_POS, LOC_NRM, LOC_COL, LOC_AUX = 0, 1, 2, 3
ATRIBUTOS = {LOC_POS: "a_pos", LOC_NRM: "a_normal", LOC_COL: "a_color", LOC_AUX: "a_aux"}
UNIFORMES = (
    "u_sun_dir", "u_sun_color", "u_ambient", "u_cam_pos",
    "u_sun_fuerza", "u_luna_dir", "u_luna_fuerza", "u_time", "u_atlas",
)
