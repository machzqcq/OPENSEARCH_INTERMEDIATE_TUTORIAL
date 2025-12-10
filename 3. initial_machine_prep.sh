#!/bin/bash

# =============================================================================
# Ubuntu Machine Preparation Script for OpenSearch Intermediate Tutorial
# =============================================================================
# This script installs all required dependencies for the OpenSearch course
# Run with: bash initial_machine_prep.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${GREEN}===================================================${NC}"
    echo -e "${GREEN} $1${NC}"
    echo -e "${GREEN}===================================================${NC}"
}

# =============================================================================
# System Configuration
# =============================================================================
print_section "🔧 Configuring System Settings"

# Increase vm.max_map_count for OpenSearch
print_status "Setting vm.max_map_count=262144..."
sudo sysctl -w vm.max_map_count=262144

# Make it permanent
if ! grep -q "vm.max_map_count=262144" /etc/sysctl.conf; then
    echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
    print_success "vm.max_map_count permanently set in /etc/sysctl.conf"
else
    print_status "vm.max_map_count already configured in /etc/sysctl.conf"
fi

# =============================================================================
# Update Package Lists
# =============================================================================
print_section "📦 Updating Package Lists"
sudo apt update  && sudo apt install -y curl libatomic1

# =============================================================================
# Install Git
# =============================================================================
print_section "🐙 Installing Git"
if command -v git &> /dev/null; then
    print_status "Git already installed: $(git --version)"
else
    sudo apt install -y git
    print_success "Git installed: $(git --version)"
fi

# =============================================================================
# Install Java (OpenJDK 21)
# =============================================================================
print_section "☕ Installing Java OpenJDK 21"
if command -v java &> /dev/null; then
    print_status "Java already installed: $(java -version 2>&1 | head -n 1)"
else
    sudo apt install -y openjdk-21-jdk
    print_success "Java installed: $(java -version 2>&1 | head -n 1)"
fi

# =============================================================================
# Install Docker
# =============================================================================
print_section "🐳 Installing Docker"
if command -v docker &> /dev/null; then
    print_status "Docker already installed: $(docker --version)"
else
    sudo apt install -y docker.io
    print_success "Docker installed: $(docker --version)"
fi

# Start and enable Docker service
print_status "Starting and enabling Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
print_success "Docker service started and enabled"

# Add user to docker group
print_status "Adding user $USER to docker group..."
sudo usermod -aG docker $USER
print_warning "You need to log out and log back in for docker group changes to take effect"

# =============================================================================
# Install uv (Python Package Manager)
# =============================================================================
print_section "🐍 Installing uv (Python Package Manager)"
if command -v uv &> /dev/null; then
    print_status "uv already installed: $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add to current session
    export PATH="$HOME/.cargo/bin:$PATH"
    print_success "uv installed"
fi

# =============================================================================
# Install Pixi (Optional)
# =============================================================================
print_section "📦 Installing Pixi (Optional Package Manager)"
if command -v pixi &> /dev/null; then
    print_status "Pixi already installed: $(pixi --version)"
else
    curl -fsSL https://pixi.sh/install.sh | bash
    print_success "Pixi installed"
fi

# =============================================================================
# Install NVM and Node.js
# =============================================================================
print_section "🔢 Installing NVM and Node.js"

# Check if nvm is already installed
if [ -d "$HOME/.nvm" ]; then
    print_status "NVM already installed"
else
    print_status "Installing NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    print_success "NVM installed"
fi

# Load nvm into current session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# source .bashrc
source ~/.bashrc

# Install Node.js
if command -v node &> /dev/null; then
    print_status "Node.js already installed: $(node --version)"
else
    print_status "Installing Node.js (latest)..."
    nvm install node
    print_success "Node.js installed: $(node --version)"
fi

# =============================================================================
# Install Mermaid CLI
# =============================================================================
print_section "📊 Installing Mermaid CLI"
if command -v mmdc &> /dev/null; then
    print_status "Mermaid CLI already installed"
else
    npm install -g @mermaid-js/mermaid-cli@10.6.1
    print_success "Mermaid CLI installed"
fi

# =============================================================================
# Optional: Install SSH Server
# =============================================================================
print_section "🔐 SSH Server Installation (Optional)"
read -p "Do you want to install and configure SSH server? (y/n): " install_ssh

if [[ $install_ssh == "y" || $install_ssh == "Y" ]]; then
    if command -v sshd &> /dev/null; then
        print_status "SSH server already installed"
    else
        sudo apt install -y openssh-server
        print_success "SSH server installed"
    fi
    
    # Start and enable SSH
    sudo systemctl start ssh
    sudo systemctl enable ssh
    print_success "SSH service started and enabled"
    
    # Configure firewall if ufw is installed
    if command -v ufw &> /dev/null; then
        sudo ufw allow ssh
        print_success "SSH allowed through firewall"
    fi
    
    print_status "SSH config location: /etc/ssh/sshd_config"
else
    print_status "Skipping SSH server installation"
fi

# =============================================================================
# Summary
# =============================================================================
print_section "✅ Installation Complete!"

echo ""
echo "Installed components:"
echo "  ✓ System configuration (vm.max_map_count)"
echo "  ✓ Git: $(git --version 2>&1 | head -n 1)"
echo "  ✓ Java: $(java -version 2>&1 | head -n 1)"
echo "  ✓ Docker: $(docker --version)"
echo "  ✓ uv: $(uv --version 2>&1 || echo 'Check after shell reload')"
echo "  ✓ Pixi: $(pixi --version 2>&1 || echo 'Check after shell reload')"
echo "  ✓ Node.js: $(node --version 2>&1 || echo 'Check after shell reload')"
echo "  ✓ npm: $(npm --version 2>&1 || echo 'Check after shell reload')"
echo "  ✓ Mermaid CLI: Installed"
[[ $install_ssh == "y" || $install_ssh == "Y" ]] && echo "  ✓ SSH Server: Installed"

echo ""
print_warning "IMPORTANT: Please complete these manual steps:"
echo "  1. Log out and log back in (or run: newgrp docker) to apply docker group changes"
echo "  2. Reload your shell: source ~/.bashrc"
echo "  3. Verify installations after reload"
echo ""
print_status "To set up Python environment for this project:"
echo "  • cd to your project directory"
echo "  • Run: uv sync"
echo "  • Activate: source .venv/bin/activate"
echo ""
print_status "To set up Pixi environment (optional):"
echo "  • cd to your project directory"
echo "  • Run: pixi install"
echo "  • Activate: pixi shell"
echo ""
print_success "Setup script completed successfully! 🎉"
