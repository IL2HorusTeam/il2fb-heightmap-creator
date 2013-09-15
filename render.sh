#!/bin/bash

# Path to map's root directory. Each map subdirectory must have raw 'heights'
# binary file and topographical map file 'topographical.png'
MAPS_ROOT=$1

for f in `find $MAPS_ROOT -mindepth 1 -maxdepth 1 -type d | sort`
do
    echo "Rendering $(basename ${f})."
    dimentions=$(file $f/topographical.png \; | awk -F, '{print $2}' | tr -d ' ' | echo --width=`sed -e 's/x/00 --height=/g'`00 )
    python heightmap_creator/render.py --src=$f/heights $dimentions
    python heightmap_creator/plains_finder.py --dir=$f
    if [ $? -ne 0 ]
    then
        exit
    fi
    mv $f/heights.jet.png $f/jet.png
    mv $f/heights.terrain.png $f/terrain.png
    echo "Done."
done
