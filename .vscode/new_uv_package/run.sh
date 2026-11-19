#!/usr/bin/env zsh

# Package Type
echo "Package type:"
echo "  [1] Basic Service"
echo "  [2] Virtual Object"
echo "  [3] Workflow"
echo "  [4] Other"
print -n "Select [1/2/3/4]: "
read type_choice

case $type_choice in
  1) prefix="sv-" ;;
  2) prefix="vo-" ;;
  3) prefix="wf-" ;;
  4) prefix="" ;;
  *) echo "Invalid package type!" && exit 1 ;;
esac

# Package Name
print -n "Package name: "
read name
[ -z "$name" ] && echo "Package name cannot be empty!" && exit 1

# Confirm
pkg="${prefix}${name}"

echo "Package to be created: $pkg"
print -n "Confirm? [y/n]: "
read confirm
[ "$confirm" != "y" ] && echo "Aborted." && exit 0
echo "Creating Package: $pkg ..."

mod=$(echo "$pkg" | tr '-' '_')

if [ "$type_choice" = "4" ]; then
  files=(models enums types utils)
else
  files=(main models enums types utils)
fi

uv init --lib "packages/$pkg" --build-backend uv_build --no-readme \
  && sed "s/{{PACKAGE_NAME}}/$pkg/g" .vscode/new_uv_package/pyproject.template.toml > "packages/$pkg/pyproject.toml" \
  && touch "packages/$pkg/src/$mod"/${^files}.py \
  && echo "Created Package: packages/$pkg"