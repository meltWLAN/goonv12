#!/bin/bash

# Exit on error
set -e

# Get current date and time in the format YYYYMMDD_HHMMSS
DATE_TAG=$(date +"%Y%m%d_%H%M%S")
BRANCH_NAME="backup_${DATE_TAG}"

echo "===== Creating backup of system to GitHub ====="
echo "Date tag: ${DATE_TAG}"
echo "Branch name: ${BRANCH_NAME}"

# Make sure we're in the main branch and up to date
echo "Updating local repository..."
git checkout main
git pull origin main

# Create a new branch for this backup
echo "Creating new branch: ${BRANCH_NAME}..."
git checkout -b ${BRANCH_NAME}

# Add all files to git (including new ones)
echo "Adding files to git..."
git add -A

# Commit with date-based message
echo "Committing changes..."
git commit -m "System backup ${DATE_TAG}"

# Push the branch to remote
echo "Pushing to GitHub..."
git push origin ${BRANCH_NAME}

# Create a tag for this backup
echo "Creating tag..."
git tag "backup_${DATE_TAG}"
git push origin "backup_${DATE_TAG}"

# Return to main branch
echo "Returning to main branch..."
git checkout main

echo "===== Backup completed successfully ====="
echo "Backup branch: ${BRANCH_NAME}"
echo "Backup tag: backup_${DATE_TAG}"
echo "You can restore this version using:"
echo "git checkout ${BRANCH_NAME}"
echo "or"
echo "git checkout backup_${DATE_TAG}" 