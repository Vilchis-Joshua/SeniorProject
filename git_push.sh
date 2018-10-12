#!/bin/bash

git add .
read answer
git commit -m "${answer}"
git push josh_sp
clear