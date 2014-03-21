IL-2 Heightmap Creator
======================

A distributed Python application with client-server architecture for making height maps of IL-2 FB locations.

Locations can have areas of thousands square kilometers. Application loads sequences of missions to multiple local or remote IL-2 dedicated servers and queries heights in parallel mode. This gives a drastic decrease in execution time which can be shorten from hours to tens of minutes.

Application creates a binary array of heights taken with a step of 100 meters. Binary data can be used to render height maps (including isolines), to highlight plains on topographic maps, etc.

You can browse results for standard locations here: https://copy.com/uKwaDtRBJKix.
