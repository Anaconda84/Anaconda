from cx_Freeze import setup, Executable

includes = ["encodings.utf_8", "encodings.latin_1", "encodings.ascii", "encodings.raw_unicode_escape"]
includefiles = [ (r"BaseLib/Images", "BaseLib/Images") ]
setup(
    nanme = "SwarmVideo",
    version = "0.8",
    description = "Swarm Video",
    options = { "build_exe": { "includes": includes,
                               "include_files": includefiles
                             }
    
              },
    executables = [Executable("BaseLib/Plugin/SwarmEngine.py")])
