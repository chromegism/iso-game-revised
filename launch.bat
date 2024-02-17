@echo off

if "%1" == "python" (
    echo:
    echo ----- OUTPUT -----
    echo:

    python build.py %2
    
) else if "%1" == "c++" (
    echo:
    echo ----- COMPILING -----
    echo:

    g++ -std=c++17 build.cpp -Iinclude -Llib -o build

    echo:
    echo ----- OUTPUT -----
    echo:

    build.exe %2

) else if "%1" == "cpp" (
    echo:
    echo ----- COMPILING -----
    echo:

    g++ -std=c++17 build.cpp -Iinclude -Llib -o build

    echo:
    echo ----- OUTPUT -----
    echo:

    build.exe %2
    
)