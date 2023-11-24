#!/bin/bash

for filename in */*.ipynb; do
	echo $filename
	jupyter nbconvert --to notebook --execute $filename
done
