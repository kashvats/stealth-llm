#!/bin/bash
cd "$(dirname "$0")"
echo "========================================================"
echo "              PROJECT RUNNER"
echo "========================================================"
echo ""
echo "Please select how you want to run the project:"
echo "1. Run Locally"
echo ""
read -p "Enter your choice: " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Starting Local Environment..."
    echo ""
    python main.py
else
    echo "Invalid choice. Exiting."
    exit 1
fi