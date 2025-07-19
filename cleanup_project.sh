#!/bin/bash
# Project Cleanup Script
# Removes obsolete debug scripts and backup files

echo "🧹 Starting NavyYard project cleanup..."

# Create backup directory if it doesn't exist
mkdir -p backup/scripts
mkdir -p backup/docs

echo "📦 Moving files to backup..."

# Move documentation to backup
mv structure.md backup/docs/ 2>/dev/null || echo "structure.md not found"

# Move utility scripts to backup
mv diagnose.sh backup/scripts/ 2>/dev/null || echo "diagnose.sh not found"
mv reset_projekt.sh backup/scripts/ 2>/dev/null || echo "reset_projekt.sh not found"

echo "🗑️  Removing GPU debug scripts..."

# Remove GPU debug scripts
rm -f fix_torch_cuda.py
rm -f gpu_autopsy.py
rm -f run_gpu_test.sh

echo "🗑️  Removing temporary/generated files..."

# Remove temporary files
rm -f llama_cpp_gpu_backup.tar.gz

echo "🗑️  Removing old config files..."

# Remove old config files
rm -f config/sage.orig

echo "📊 Cleanup summary:"
echo "✅ Moved documentation to backup/docs/"
echo "✅ Moved utility scripts to backup/scripts/"
echo "✅ Removed $(echo fix_torch_cuda.py gpu_autopsy.py run_gpu_test.sh | wc -w) GPU debug scripts"
echo "✅ Removed temporary and old config files"

echo ""
echo "🎉 Project cleanup completed!"
echo "📁 Core functionality preserved:"
echo "   - Main application (main.py, run.sh, etc.)"
echo "   - Chatbot core modules"
echo "   - Test suite"
echo "   - Configuration files"
echo ""
echo "📦 Archived files can be found in backup/ directory"