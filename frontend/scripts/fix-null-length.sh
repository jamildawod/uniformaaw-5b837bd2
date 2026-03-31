#!/bin/bash

FILES=$(grep -R "\.length" /opt/uniforma/frontend/components -l)

for file in $FILES; do
  sed -i 's/\([a-zA-Z0-9_?.]\+\)\.length/(\1 || []).length/g' "$file"
done

echo "DONE fixing .length"
