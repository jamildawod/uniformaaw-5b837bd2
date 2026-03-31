#!/bin/bash

FILES=$(grep -R "\.map(" /opt/uniforma/frontend/components -l)

for file in $FILES; do
  sed -i 's/\([a-zA-Z0-9_?.]\+\)\.map(/(\1 || []).map(/g' "$file"
done

echo "DONE fixing .map"
