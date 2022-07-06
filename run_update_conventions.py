# This is a convenience script to run the update_conventions() function.
# The function is part of the sofar package (https://pyfar.org/) but needs
# to be run from within this repo to update it to the latest changes in the
# Matlab/Octave API (https://github.com/sofacoustics/API_MO)
from update_conventions import update_conventions

update_conventions()
