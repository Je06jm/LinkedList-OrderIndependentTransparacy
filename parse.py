import sys

path = sys.argv[1]
print(path)

file = open(path, "r")
lines = file.readlines()
file.close()

defines = {}
functions = {}
names = {}
name_defines = {}

processed = ""

for line in lines:
    if not line.startswith("#define gl"):
        processed += line
    try:
        line = line.replace("(", " ")
        line = line.replace(")", " ")
        if line.startswith("#define GL"):
            p = line.split()
            defines[p[1]] = p[2]
    
        elif line.startswith("typedef"):
            p = line.split()
            params = ""
            pparms = p[4:-1]
            for i in range(len(pparms)):
                params += pparms[i] + " "
            params = params[:-1]
            functions[p[3]] = {"returns" : p[1], "params" : params}
    
        elif line.startswith("GLAPI"):
            p = line.split()
            names[p[1]] = p[2][:-1]
    
        elif line.startswith("#define gl"):
            p = line.split()
            name_defines[p[2]] = p[1]
        
    except Exception:
        pass

pyfile = ""

for function in functions:
    try:
        glad_name = names[function]
        gl_name = name_defines[glad_name]
        pyfile += gl_name + " = __late_load(\"" + gl_name + "\", \"" + functions[function]["returns"] + "\", \""
        pyfile += functions[function]["params"] + "\")\n"
    
    except Exception:
        pass

pyfile += "\n"

for define in defines:
    pyfile += define + " = " + defines[define] + "\n"

file = open("pyfile.py", "w")
file.write(pyfile)
file.close()
