#!/bin/bash

TEST_DIR="test/api_tests"

if [ -d "$TEST_DIR" ]; then
  find "$TEST_DIR" -type f -name "*.py" -exec pytest --cov=server --cov-report=html -s {} +
else
  echo "Директория $TEST_DIR не существует."
  exit 1
fi