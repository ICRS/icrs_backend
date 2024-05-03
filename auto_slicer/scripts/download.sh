#!/bin/bash

wget -O bambu.zip https://github.com/bambulab/BambuStudio/archive/refs/tags/v01.09.01.58.zip  

unzip bambu.zip  "BambuStudio-01.09.01.58/resources/profiles/BBL/*"
rm bambu.zip

mv BambuStudio-01.09.01.58/resources/profiles/BBL BBL
rm BambuStudio-01.09.01.58 -r

python merge.py

<!-- rm -rf BBL -->
