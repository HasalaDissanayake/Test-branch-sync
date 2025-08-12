#!/bin/bash

# Configurable variables
SOURCE_BRANCH="dummy"
TARGET_BRANCH="main"
REMOTE="origin"  # Your Bitbucket remote name
COMMIT_MESSAGE="Update main with selected released files from ${SOURCE_BRANCH}"

# Check if file paths are provided as arguments
if [ $# -eq 0 ]; then
  echo "Error: No file paths provided."
  echo "Usage: $0 <file_path1> <file_path2> ..."
  echo "Example: $0 origination/test.js config/fd_certificate.js"
  exit 1
fi

# Ensure we're starting from the source branch
if [ "$(git rev-parse --abbrev-ref HEAD)" != "${SOURCE_BRANCH}" ]; then
  echo "Error: Must be on ${SOURCE_BRANCH} branch to run this script."
  exit 1
fi

# Switch to target branch and pull latest
git checkout ${TARGET_BRANCH}
if [ $? -ne 0 ]; then
  echo "Error: Failed to checkout ${TARGET_BRANCH}."
  exit 1
fi

git pull ${REMOTE} ${TARGET_BRANCH}
if [ $? -ne 0 ]; then
  echo "Error: Failed to pull latest from ${TARGET_BRANCH}."
  exit 1
fi

# Get git diff output for validation
DIFF_OUTPUT=$(git diff --name-status ${TARGET_BRANCH}..${SOURCE_BRANCH} | grep '^[AM]')

# Track valid and invalid files
VALID_FILES=()
INVALID_FILES=()

# Validate each provided file path
for FILE in "$@"; do
  # Check if the file exists in git diff with A or M status
  if echo "${DIFF_OUTPUT}" | grep -q "^[AM][[:space:]]${FILE}$"; then
    VALID_FILES+=("${FILE}")
  else
    INVALID_FILES+=("${FILE}")
  fi
done

# Check if there are any valid files to process
if [ ${#VALID_FILES[@]} -eq 0 ]; then
  echo "No valid files (with A or M status) provided. Nothing to update."
  if [ ${#INVALID_FILES[@]} -gt 0 ]; then
    echo "Invalid or non-matching files:"
    printf '%s\n' "${INVALID_FILES[@]}"
  fi
  git checkout ${SOURCE_BRANCH}
  exit 0
fi

# Process each valid file
for FILE in "${VALID_FILES[@]}"; do
  git checkout ${SOURCE_BRANCH} -- "${FILE}"
  git add "${FILE}"
done

# Report invalid files, if any
if [ ${#INVALID_FILES[@]} -gt 0 ]; then
  echo "Warning: The following files were skipped (not found in git diff with A or M status):"
  printf '%s\n' "${INVALID_FILES[@]}"
fi

# Commit the changes
git commit -m "${COMMIT_MESSAGE}"
if [ $? -ne 0 ]; then
  echo "Error: Commit failed (possibly no changes after processing)."
  git checkout ${SOURCE_BRANCH}
  exit 1
fi

# Push to remote
git push ${REMOTE} ${TARGET_BRANCH}
if [ $? -ne 0 ]; then
  echo "Error: Push to ${REMOTE}/${TARGET_BRANCH} failed."
  git checkout ${SOURCE_BRANCH}
  exit 1
fi

# Switch back to source branch
git checkout ${SOURCE_BRANCH}

echo "Success: ${TARGET_BRANCH} updated with ${#VALID_FILES[@]} selected files from ${SOURCE_BRANCH} and pushed to Bitbucket."
if [ ${#VALID_FILES[@]} -gt 0 ]; then
  echo "Processed files:"
  printf '%s\n' "${VALID_FILES[@]}"
fi