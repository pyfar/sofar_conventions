# sofar conventions

 SOFA conventions of the official Matlab/Octave API (SOFAtoolbox) as json
 files. SOFA conventions are the basis of SOFA files, a data format to store
 spatially distributed acoustic data.

 The function `update_conventions()` reads the official conventions from
 SOFAtoolbox available as csv files from https://github.com/sofacoustics/SOFAtoolbox/tree/master/SOFAtoolbox/conventions
 and converts them to json files. During the conversion some Matlab/Octave
 specific values in the csv files are converted to Python specific values.

 The conventions and functions are tested as part of the sofar package available
 from https://github.com/pyfar/sofar

**References**

AES69-2020: *AES standard for file exchange - Spatial acoustic data file
format*, Audio Engineering Society, Inc., New York, NY, USA.
