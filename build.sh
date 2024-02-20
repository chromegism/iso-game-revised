if [ "$1" == "python" ]
then
    echo
    echo "----- OUTPUT -----"
    echo

    python3 main.py $2
fi

if [ "$1" == "c++" ]
then
    echo
    echo "----- COMPILING -----"
    echo

    g++ main.cpp -Wall -lSDL2main -lSDL2 -lSDL2_image -o main_deb

    echo
    echo "----- OUTPUT -----"
    echo

    ./main_deb
fi

if [ "$1" == "cpp" ]
then
    echo
    echo "----- COMPILING -----"
    echo

    g++ main.cpp -Wall -lSDL2main -lSDL2 -lSDL2_image -o main_deb

    echo
    echo "----- OUTPUT -----"
    echo

    ./main_deb
fi