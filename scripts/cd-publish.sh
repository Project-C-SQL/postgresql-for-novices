#!/usr/bin/env bash

# based on:
# https://github.com/python-poetry/poetry/issues/3670#issuecomment-776462445

if [ "$GITHUB_REF" = "refs/heads/main" ]; then
  poetry version $(poetry version --short).$GITHUB_RUN_NUMBER
else
  poetry version $(poetry version --short)-dev.$GITHUB_RUN_NUMBER
  # or use --repository testpypi ?
  # in case collisions etc. occur
  # (requires a testpypi setup)
fi
echo -e "\nPublishing to version ref '$(poetry version --short)'...\n\n"
poetry publish --no-interaction --build -u $PYPI_USER -p $PYPI_PASS
