# Integrated Margin Maximizer

## How to Deploy:

1. Make sure Docker Daemon is running
2. Build Docker Image: `docker build --platform linux/amd64 -t margin_max .`
   1. Note: The above command is to build image for Azure App Service deployment. 
   2. For local deployment - `docker build -t margin_max`
3. Run Docker: `docker run -d -p 8501:8501 --name margin_max_container margin_max`
4. Pushing Image to ACR
   1. Install az login `brew install azure-cli` for MAC
   2. Login to current Azure A/c - `az login`
   3. Container Registry Name - `integratedmarginmaximizer`
   4. Login into desired Azure Container Registry - `az acr login --name integratedmarginmaximizer`
   5. Tag Docker Image: `docker tag margin_max integratedmarginmaximizer.azurecr.io/margin_max:latest`
   6. Pushing Docker Image: `docker push integratedmarginmaximizer.azurecr.io/margin_max:latest`

### Configuring App Service
#### Config:
1. OS - Linux
2. Tier - P1V3
3. Container - ACR
4. Select Registry
5. Add Image Name - `margin_max`
6. Add Tag Name - `latest`
7. Expose Streamlit port - `8501`
8. No startup commands to be added