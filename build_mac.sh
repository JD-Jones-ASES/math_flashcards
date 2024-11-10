#!/bin/bash

# Exit on error
set -e

# Function to clean build directories
clean_build() {
    echo "Cleaning build directories..."
    rm -rf build dist
}

# Function to check necessary tools
check_requirements() {
    if ! command -v pyinstaller &> /dev/null; then
        echo "Error: pyinstaller not found. Please install build requirements."
        exit 1
    fi
    if ! command -v lipo &> /dev/null; then
        echo "Error: lipo not found. Please install Xcode command line tools."
        exit 1
    }
}

echo "Checking build requirements..."
check_requirements

# Clean previous builds
clean_build

# Build for Intel
echo "Building for Intel (x86_64)..."
export ARCH_TARGET="x86_64"
pyinstaller main.spec
mv "dist/MathFlashcards.app" "dist/MathFlashcards-x86_64.app"

# Clean intermediates
rm -rf build

# Build for Apple Silicon
echo "Building for Apple Silicon (arm64)..."
export ARCH_TARGET="arm64"
pyinstaller main.spec
mv "dist/MathFlashcards.app" "dist/MathFlashcards-arm64.app"

# Create universal binary
echo "Creating universal binary..."
mkdir -p "dist/MathFlashcards.app/Contents/MacOS"

# Create universal binary using lipo
echo "Combining architectures with lipo..."
lipo "dist/MathFlashcards-x86_64.app/Contents/MacOS/MathFlashcards" \
     "dist/MathFlashcards-arm64.app/Contents/MacOS/MathFlashcards" \
     -create -output "dist/MathFlashcards.app/Contents/MacOS/MathFlashcards"

# Copy additional resources from arm64 build (they're identical between architectures)
echo "Copying resources and metadata..."
cp -R "dist/MathFlashcards-arm64.app/Contents/Resources" "dist/MathFlashcards.app/Contents/"
cp -R "dist/MathFlashcards-arm64.app/Contents/Info.plist" "dist/MathFlashcards.app/Contents/"
cp -R "dist/MathFlashcards-arm64.app/Contents/Frameworks" "dist/MathFlashcards.app/Contents/" 2>/dev/null || true

# Clean up intermediate builds
echo "Cleaning up intermediate builds..."
rm -rf "dist/MathFlashcards-x86_64.app" "dist/MathFlashcards-arm64.app"

# Set permissions
echo "Setting permissions..."
chmod +x "dist/MathFlashcards.app/Contents/MacOS/MathFlashcards"

echo "Universal binary build complete!"
echo "Output: dist/MathFlashcards.app"

# Print architecture verification
echo "Verifying architectures..."
lipo -info "dist/MathFlashcards.app/Contents/MacOS/MathFlashcards"
