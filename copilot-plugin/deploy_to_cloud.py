"""
Script để deploy IRIS Copilot Plugin lên cloud services
"""
import os
import subprocess
import json
import sys
from typing import Dict, Any

class CloudDeployer:
    """Cloud deployment manager"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_file = "deploy_config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                return json.load(f)
        else:
            return self.create_default_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        config = {
            "azure": {
                "enabled": False,
                "resource_group": "iris-rg",
                "app_name": "iris-copilot-plugin",
                "plan_name": "iris-plan",
                "region": "Southeast Asia"
            },
            "aws": {
                "enabled": False,
                "app_name": "iris-copilot-plugin",
                "region": "ap-southeast-1",
                "environment": "production"
            },
            "gcp": {
                "enabled": False,
                "project_id": "iris-project",
                "service_name": "iris-copilot-plugin",
                "region": "asia-southeast1"
            },
            "vps": {
                "enabled": False,
                "domain": "copilot.iris.pnj.com.vn",
                "server_ip": "YOUR_SERVER_IP"
            }
        }
        
        with open("deploy_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Created deploy_config.json")
        print("📝 Please edit the configuration before deploying")
        return config
    
    def deploy_to_azure(self):
        """Deploy to Azure App Service"""
        print("🚀 Deploying to Azure App Service...")
        
        try:
            # Check Azure CLI
            subprocess.run(["az", "--version"], check=True, capture_output=True)
            
            # Create resource group if not exists
            subprocess.run([
                "az", "group", "create",
                "--name", self.config["azure"]["resource_group"],
                "--location", self.config["azure"]["region"]
            ], check=True)
            
            # Create app service plan
            subprocess.run([
                "az", "appservice", "plan", "create",
                "--name", self.config["azure"]["plan_name"],
                "--resource-group", self.config["azure"]["resource_group"],
                "--sku", "B1",
                "--is-linux"
            ], check=True)
            
            # Create web app
            subprocess.run([
                "az", "webapp", "create",
                "--name", self.config["azure"]["app_name"],
                "--resource-group", self.config["azure"]["resource_group"],
                "--plan", self.config["azure"]["plan_name"],
                "--runtime", "PYTHON|3.11"
            ], check=True)
            
            # Configure environment variables
            env_vars = [
                "IRIS_API_URL=https://iris.pnj.com.vn",
                "IRIS_API_BASE_URL=https://iris.pnj.com.vn/api/v1",
                "AZURE_AD_CLIENT_ID=${AZURE_AD_CLIENT_ID}",
                "AZURE_AD_CLIENT_SECRET=${AZURE_AD_CLIENT_SECRET}",
                "AZURE_AD_TENANT_ID=${AZURE_AD_TENANT_ID}",
                "PLUGIN_SECRET=${PLUGIN_SECRET}"
            ]
            
            for var in env_vars:
                subprocess.run([
                    "az", "webapp", "config", "appsettings", "set",
                    "--name", self.config["azure"]["app_name"],
                    "--resource-group", self.config["azure"]["resource_group"],
                    "--settings", var
                ], check=True)
            
            # Deploy code
            subprocess.run([
                "az", "webapp", "deployment", "source", "config-local-git",
                "--name", self.config["azure"]["app_name"],
                "--resource-group", self.config["azure"]["resource_group"]
            ], check=True)
            
            print("✅ Azure deployment completed!")
            print(f"🌐 App URL: https://{self.config['azure']['app_name']}.azurewebsites.net")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Azure deployment failed: {e}")
        except FileNotFoundError:
            print("❌ Azure CLI not found. Please install Azure CLI first.")
    
    def deploy_to_aws(self):
        """Deploy to AWS Elastic Beanstalk"""
        print("🚀 Deploying to AWS Elastic Beanstalk...")
        
        try:
            # Check EB CLI
            subprocess.run(["eb", "--version"], check=True, capture_output=True)
            
            # Initialize EB application
            subprocess.run([
                "eb", "init", self.config["aws"]["app_name"],
                "--platform", "python-3.11",
                "--region", self.config["aws"]["region"]
            ], check=True)
            
            # Create environment
            subprocess.run([
                "eb", "create", self.config["aws"]["environment"],
                "--instance-type", "t3.micro",
                "--single-instance"
            ], check=True)
            
            # Deploy
            subprocess.run(["eb", "deploy"], check=True)
            
            print("✅ AWS deployment completed!")
            print("🌐 Check EB console for the application URL")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ AWS deployment failed: {e}")
        except FileNotFoundError:
            print("❌ EB CLI not found. Please install EB CLI first.")
    
    def deploy_to_gcp(self):
        """Deploy to Google Cloud Run"""
        print("🚀 Deploying to Google Cloud Run...")
        
        try:
            # Check gcloud CLI
            subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
            
            # Set project
            subprocess.run([
                "gcloud", "config", "set", "project", self.config["gcp"]["project_id"]
            ], check=True)
            
            # Deploy to Cloud Run
            subprocess.run([
                "gcloud", "run", "deploy", self.config["gcp"]["service_name"],
                "--source", ".",
                "--platform", "managed",
                "--region", self.config["gcp"]["region"],
                "--allow-unauthenticated",
                "--set-env-vars", "IRIS_API_URL=https://iris.pnj.com.vn,IRIS_API_BASE_URL=https://iris.pnj.com.vn/api/v1"
            ], check=True)
            
            print("✅ GCP deployment completed!")
            print("🌐 Check Cloud Run console for the service URL")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ GCP deployment failed: {e}")
        except FileNotFoundError:
            print("❌ gcloud CLI not found. Please install Google Cloud SDK first.")
    
    def deploy_to_vps(self):
        """Deploy to VPS/Server"""
        print("🚀 Deploying to VPS/Server...")
        
        print("📋 Manual deployment steps for VPS:")
        print("1. Upload code to server")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Configure environment variables")
        print("4. Setup Nginx reverse proxy")
        print("5. Configure SSL certificate")
        print("6. Start application with systemd")
        
        # Generate deployment script
        self.generate_vps_script()
    
    def generate_vps_script(self):
        """Generate VPS deployment script"""
        script_content = f"""#!/bin/bash
# VPS Deployment Script for IRIS Copilot Plugin

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx

# Create application directory
sudo mkdir -p /opt/iris-copilot-plugin
sudo chown $USER:$USER /opt/iris-copilot-plugin

# Copy application files (manual step)
# scp -r . user@server:/opt/iris-copilot-plugin/

# Install Python dependencies
cd /opt/iris-copilot-plugin
pip3 install -r requirements.txt

# Create environment file
cat > .env << EOF
IRIS_API_URL=https://iris.pnj.com.vn
IRIS_API_BASE_URL=https://iris.pnj.com.vn/api/v1
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id
PLUGIN_SECRET=your-plugin-secret
DEBUG=false
ENVIRONMENT=production
EOF

# Create systemd service
sudo tee /etc/systemd/system/iris-copilot-plugin.service > /dev/null << EOF
[Unit]
Description=IRIS Copilot Plugin
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/iris-copilot-plugin
Environment=PATH=/opt/iris-copilot-plugin/venv/bin
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/iris-copilot-plugin > /dev/null << EOF
server {{
    listen 80;
    server_name {self.config['vps']['domain']};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.config['vps']['domain']};
    
    location / {{
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/iris-copilot-plugin /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d {self.config['vps']['domain']}

# Start application
sudo systemctl enable iris-copilot-plugin
sudo systemctl start iris-copilot-plugin

echo "✅ VPS deployment completed!"
echo "🌐 Application URL: https://{self.config['vps']['domain']}"
"""
        
        with open("deploy_vps.sh", "w") as f:
            f.write(script_content)
        
        os.chmod("deploy_vps.sh", 0o755)
        print("✅ Generated deploy_vps.sh script")
        print("📝 Run this script on your VPS server")
    
    def show_menu(self):
        """Show deployment menu"""
        print("\n🚀 IRIS Copilot Plugin Cloud Deployment")
        print("=" * 50)
        print("1. Deploy to Azure App Service")
        print("2. Deploy to AWS Elastic Beanstalk")
        print("3. Deploy to Google Cloud Run")
        print("4. Deploy to VPS/Server")
        print("5. Configure deployment settings")
        print("6. Exit")
        
        choice = input("\nSelect deployment option (1-6): ")
        
        if choice == "1":
            self.deploy_to_azure()
        elif choice == "2":
            self.deploy_to_aws()
        elif choice == "3":
            self.deploy_to_gcp()
        elif choice == "4":
            self.deploy_to_vps()
        elif choice == "5":
            print("📝 Edit deploy_config.json to configure deployment settings")
        elif choice == "6":
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please try again.")
            self.show_menu()

def main():
    """Main function"""
    deployer = CloudDeployer()
    deployer.show_menu()

if __name__ == "__main__":
    main()
