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

    g++ -std=c++17 build.cpp -I"C:\Cincludes64" -L"C:\Clibs64" -Wall -lSDL2main -lSDL2 -lSDL2_image -o build

    echo:
    echo ----- OUTPUT -----
    echo:

    build.exe %2

) else if "%1" == "cpp" (
    echo:
    echo ----- COMPILING -----
    echo:

    g++ -std=c++17 build.cpp -I"C:\Cincludes32" -L"C:\Clibs32" -Wall -lmingw32 -lSDL2main -lSDL2 -o build

    echo:
    echo ----- OUTPUT -----
    echo:

    build.exe %2

)