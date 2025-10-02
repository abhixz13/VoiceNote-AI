#!/bin/bash

# VoiceNote AI Development Setup Script
# This script helps set up the development environment securely

set -e  # Exit on any error

echo "🚀 Setting up VoiceNote AI development environment..."

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the VoiceNote AI project root directory"
    exit 1
fi

# Install pre-commit hooks for security
echo "🔒 Installing security pre-commit hooks..."
if command -v pip3 &> /dev/null; then
    pip3 install pre-commit detect-secrets
elif command -v pip &> /dev/null; then
    pip install pre-commit detect-secrets
else
    echo "⚠️  pip not found. Please install Python and pip first."
    echo "   You can install pre-commit manually: pip install pre-commit detect-secrets"
fi

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  pre-commit not found. Security hooks not installed."
fi

# Set up backend environment
echo "📝 Setting up backend environment..."
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/env.example" ]; then
        cp backend/env.example backend/.env
        echo "✅ Created backend/.env from template"
        echo "⚠️  IMPORTANT: Please edit backend/.env and add your actual API keys"
        echo "   - Get Supabase keys from: https://app.supabase.com/project/YOUR_PROJECT/settings/api"
        echo "   - Get OpenAI key from: https://platform.openai.com/api-keys"
    else
        echo "❌ backend/env.example not found"
    fi
else
    echo "✅ backend/.env already exists"
fi

# Check for common security issues
echo "🔍 Running security checks..."

# Check if .env files are in .gitignore
if grep -q "\.env" .gitignore; then
    echo "✅ .env files are properly ignored in .gitignore"
else
    echo "⚠️  .env files might not be properly ignored. Check .gitignore"
fi

# Check for any accidentally committed secrets
if command -v detect-secrets &> /dev/null; then
    echo "🔍 Scanning for accidentally committed secrets..."
    detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins
    echo "✅ Secret scan completed"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your actual API keys"
echo "2. Install dependencies: npm install && cd backend && pip install -r requirements.txt"
echo "3. Start development: npm run dev (frontend) and uvicorn main:app --reload (backend)"
echo ""
echo "🔒 Security reminders:"
echo "- Never commit .env files"
echo "- Use different keys for development and production"
echo "- Regularly rotate your API keys"
echo "- The pre-commit hooks will scan for secrets before each commit"
echo ""
