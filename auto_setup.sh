#!/bin/bash

# Command to run this script:
# $ sudo chmod +x auto_setup.sh && sudo ./auto_setup.sh

# Check if script is running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Create the service directory under /opt/bluelink
echo "Creating /opt/bluelink directory..."
mkdir -p /opt/bluelink

echo "Moving scripts to /opt/bluelink/bluelink and making the files executable..."
# Move all scripts to the package directory and make them executable
cp -f *.py /opt/bluelink/
chmod +x /opt/bluelink/*.py

# Move the systemd service file to the systemd directory
echo "Moving the service file to /etc/systemd/system..."
cp -f "bluelink.service" "/etc/systemd/system/bluelink.service"

# Create a symbolic link to the CLI script in /usr/local/bin
echo "Creating symbolic link for CLI script..."
ln -sf /opt/bluelink/cli.py /usr/local/bin/bluelink

# Reload systemd manager configuration
echo "Reloading systemctl daemon..."
systemctl daemon-reload

# Prompt user to enable bluelink service at startup
while true; do
    read -p "Do you want to enable bluelink at startup? [y/n] (Default=y): " response
    response="${response,,}"  # Convert response to lowercase

    if [[ "$response" == "y" || "$response" == "yes" || "$response" == "" ]]; then
        echo "Enabling bluelink service using systemctl..."
        systemctl enable bluelink
        break
    elif [[ "$response" == "n" || "$response" == "no" ]]; then
        echo "Not enabling bluelink service at startup."
        break
    else
        echo "Invalid input. Please enter y (yes) or n (no)."
    fi
done

echo ""
echo "You can use the CLI by running the command 'bluelink'."
echo "This file can be safely removed."
echo "Setup completed."
