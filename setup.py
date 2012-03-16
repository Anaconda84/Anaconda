from cx_Freeze import setup, Executable

setup(
    nanme = "SwarmVideo",
    version = "0.8",
    description = "Swarm Video",
    executables = [Executable("BaseLib/Plugin/SwarmEngine.py")])
    