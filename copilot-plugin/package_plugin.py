"""
Script để package IRIS Copilot Plugin cho Microsoft Copilot Studio
"""
import os
import json
import zipfile
import shutil
from pathlib import Path

def create_plugin_package():
    """Tạo plugin package cho Microsoft Copilot Studio"""
    
    print("📦 Creating IRIS Copilot Plugin package...")
    
    # Plugin files cần thiết
    required_files = [
        "manifest.json",
        "plugin.json", 
        "openapi.json",
        "icons/outline.png",
        "icons/color.png"
    ]
    
    # Kiểm tra files tồn tại
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please ensure all required files are present before packaging.")
        return False
    
    # Tạo thư mục temp cho package
    temp_dir = "temp_plugin_package"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Copy required files
        for file_path in required_files:
            dest_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)
            print(f"✅ Copied: {file_path}")
        
        # Tạo ZIP file
        zip_filename = "iris-copilot-plugin.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
                    print(f"📁 Added to ZIP: {arcname}")
        
        print(f"\n✅ Plugin package created successfully: {zip_filename}")
        print(f"📁 Package size: {os.path.getsize(zip_filename) / 1024:.2f} KB")
        
        # Cleanup temp directory
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

def validate_manifest():
    """Validate manifest.json"""
    print("\n🔍 Validating manifest.json...")
    
    try:
        with open("manifest.json", "r") as f:
            manifest = json.load(f)
        
        # Kiểm tra các trường bắt buộc
        required_fields = [
            "manifestVersion", "version", "id", "packageName",
            "developer", "name", "description", "icons",
            "permissions", "validDomains", "webApplicationInfo",
            "copilotExtensions"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in manifest:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ Manifest validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Manifest validation failed: {e}")
        return False

def validate_plugin_config():
    """Validate plugin.json"""
    print("\n🔍 Validating plugin.json...")
    
    try:
        with open("plugin.json", "r") as f:
            plugin_config = json.load(f)
        
        # Kiểm tra các trường bắt buộc
        required_fields = [
            "schema", "apiVersion", "nameForHuman", "nameForModel",
            "descriptionForHuman", "descriptionForModel", "auth", "api"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in plugin_config:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ Plugin config validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Plugin config validation failed: {e}")
        return False

def create_deployment_guide():
    """Tạo deployment guide"""
    print("\n📝 Creating deployment guide...")
    
    guide_content = """# IRIS Copilot Plugin Deployment Guide

## Prerequisites
- Microsoft Copilot Studio access
- Azure AD App Registration completed
- Plugin package ready (iris-copilot-plugin.zip)

## Deployment Steps

### 1. Access Microsoft Copilot Studio
1. Go to https://web.powerva.microsoft.com/
2. Sign in with your Microsoft 365 account
3. Navigate to "Plugins" section

### 2. Upload Plugin
1. Click "Add plugin"
2. Select "Upload plugin"
3. Choose the iris-copilot-plugin.zip file
4. Click "Upload"

### 3. Configure Authentication
1. In plugin settings, configure OAuth2:
   - Client ID: [Your Azure AD App ID]
   - Client Secret: [Your Azure AD Client Secret]
   - Authorization URL: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
   - Token URL: https://login.microsoftonline.com/common/oauth2/v2.0/token
   - Scope: https://graph.microsoft.com/User.Read https://graph.microsoft.com/Team.ReadBasic.All https://graph.microsoft.com/Channel.ReadBasic.All https://graph.microsoft.com/ChannelMessage.Send

### 4. Test Plugin
1. Go to "Test" section
2. Try sample queries:
   - "Show me my teams"
   - "Search for AI documents"
   - "Help me understand machine learning"

### 5. Publish Plugin
1. Review all settings
2. Click "Publish"
3. Plugin will be available to users

## Troubleshooting

### Common Issues
1. **Authentication errors**: Check Azure AD configuration
2. **API errors**: Verify IRIS API is accessible
3. **Plugin not loading**: Check manifest.json validation

### Support
- Email: support@iris.pnj.com.vn
- Documentation: https://iris.pnj.com.vn/docs
"""
    
    with open("DEPLOYMENT_GUIDE.md", "w") as f:
        f.write(guide_content)
    
    print("✅ Deployment guide created: DEPLOYMENT_GUIDE.md")

def main():
    """Main function"""
    print("🚀 IRIS Copilot Plugin Packaging Tool")
    print("=" * 50)
    
    # Validate configurations
    if not validate_manifest():
        print("❌ Manifest validation failed. Please fix issues before packaging.")
        return
    
    if not validate_plugin_config():
        print("❌ Plugin config validation failed. Please fix issues before packaging.")
        return
    
    # Create package
    if create_plugin_package():
        print("\n🎉 Plugin packaging completed successfully!")
        print("\nNext steps:")
        print("1. Upload iris-copilot-plugin.zip to Microsoft Copilot Studio")
        print("2. Configure authentication settings")
        print("3. Test the plugin")
        print("4. Publish to users")
        
        # Create deployment guide
        create_deployment_guide()
        
    else:
        print("\n❌ Plugin packaging failed. Please check the errors above.")

if __name__ == "__main__":
    main()
