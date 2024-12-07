#!env bash

question_classes=$(grep register src/premade_questions/*.py -a1 | grep -v basic.py | grep class | sed 's/.*class //g' | sed 's/(.*//g' | sed 's/:.*//g')

for class in $question_classes ; do
  echo "name: \"(Ungraded) $(echo $class | sed 's/Question//g')\""
  echo "practice: False"
  echo "questions:"
  echo "  1:"
  echo "    $(echo $class | sed 's/Question//g'):"
  echo "      class: $class"
  echo "      repeat: 5"
  echo "---"
done > all_classes.yaml

# A hack to get rid of those dashes at the end
sed -i '' '$d' all_classes.yaml
