#!/bin/bash

# Command to run this script:
# $ sudo chmod +x auto_setup.sh && sudo ./auto_setup.sh

# Check if script is running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Create the service directory under /opt/bluelink/bluelink
echo "Creating /opt/bluelink/bluelink directory..."
sudo mkdir -p /opt/bluelink/bluelink

echo "Moving scripts to /opt/bluelink/bluelink and making them executable..."
# Move all scripts to the package directory and make them executable
sudo cp bluelink_manage.py /opt/bluelink/bluelink/
sudo cp bluelink_shared.py /opt/bluelink/bluelink/
sudo cp bluelink_system_logs.py /opt/bluelink/bluelink/
sudo cp bluelink_service.py /opt/bluelink/bluelink/
sudo chmod +x /opt/bluelink/bluelink/*.py

# Create a symbolic link to the CLI script in /usr/local/bin
echo "Creating symbolic link for CLI script..."
sudo ln -sf /opt/bluelink/bluelink/bluelink_service.py /usr/local/bin/bluelink

# Move the systemd service file to the systemd directory
echo "Moving the service file to /etc/systemd/system..."
sudo cp bluelink.service /etc/systemd/system/bluelink.service

# Reload systemd manager configuration
echo "Reloading systemctl daemon..."
sudo systemctl daemon-reload

# Prompt user to enable bluelink service at startup
while true; do
    read -p "Do you want to enable bluelink at startup? [y/n] (Default=y): " response
    response="${response,,}"  # Convert response to lowercase

    if [[ "$response" == "y" || "$response" == "yes" || "$response" == "" ]]; then
        echo "Enabling bluelink service using systemctl..."
        sudo systemctl enable bluelink
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
echo "Setup completed successfully."
