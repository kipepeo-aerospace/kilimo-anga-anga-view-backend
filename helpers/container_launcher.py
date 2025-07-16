from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (
    ContainerGroup,
    Container,
    ResourceRequests,
    ResourceRequirements,
    OperatingSystemTypes,
    ImageRegistryCredential,
    ContainerGroupRestartPolicy,
    EnvironmentVariable,
)
import logging

############################################### 
# Azure Container Instance setup
###############################################
ACR_RESOURCE_GROUP="KilimoAnga"
ACR_LOCATION="eastus"
ACR_CPU=2
ACR_MEMORY=4.0
ACR_RESTART_POLICY="Never"
ACR_OS_TYPE="Linux"


###############################################
# Initialize Azure credentials
###############################################
credential = DefaultAzureCredential()


###############################################
# Function to call the pipeline via ACR
###############################################

def start_processing_container(app, client_id: str, farm_id: str, job_id: str, vegetation_index: str):
    
    print(f"Launching container with clientId={client_id}, farmId={farm_id}, index={vegetation_index}")

    # Get the Azure subscription ID from app state
    subscription_id = app.state.azure_subscription_id

    # Identify ACR holding the pipeline image
    acr_login_server = app.state.acr_registry_server
    acr_username = app.state.acr_registry_username
    acr_password = app.state.acr_registry_password
    acr_image = app.state.acr_image

    # Get the Azure Storage connection string and container names from app state
    conn_str = app.state.azure_storage_connection_string
    raw_container = app.state.raw_images_container
    tiff_container = app.state.tiff_container
    mosaic_container = app.state.mosaic_container
    indices_container = app.state.indices_container

    # Initialize the Container Instance Management Client
    client = ContainerInstanceManagementClient(credential, subscription_id)

    # Define the container group and container details
    # Use job_id to create a unique container name and group name
    # This ensures that each job runs in its own isolated container group

    image = f"{acr_image}"
    container_name = f"anga-{job_id}".lower()
    group_name = f"job-{job_id}"

    # Define environment variables for the container
    env_vars = [
        EnvironmentVariable(name="CLIENT_ID", value=client_id),
        EnvironmentVariable(name="FIELD_ID", value=farm_id),
        EnvironmentVariable(name="VEGETATION_INDEX", value=vegetation_index),
        EnvironmentVariable(name="AZURE_STORAGE_CONNECTION_STRING", value=conn_str),
        EnvironmentVariable(name="RAW_IMAGES_CONTAINER", value=raw_container),
        EnvironmentVariable(name="TIFF_CONTAINER", value=tiff_container),
        EnvironmentVariable(name="MOSAIC_CONTAINER", value=mosaic_container),
        EnvironmentVariable(name="INDICES_CONTAINER", value=indices_container),
    ]

    # Define resource requirements for the container
    resources = ResourceRequirements(
        requests=ResourceRequests(cpu=2.0, memory_in_gb=4.0)
    )

    # Create the container instance
    # Use the Container class to define the container properties
    # The container will run the specified image with the defined environment variables
    container = Container(
        name=container_name,
        image=image,
        resources=resources,
        environment_variables=env_vars,
    )
    
    # ACI needs container group
    group = ContainerGroup(
        location="South Africa North",
        containers=[container],
        os_type=OperatingSystemTypes.linux,
        image_registry_credentials=[
            ImageRegistryCredential(
                server=acr_login_server,
                username=acr_username,
                password=acr_password,
            )
        ],
        restart_policy=ContainerGroupRestartPolicy.never,
    )

    # The API callto create and run the container group
    # This will start the container with the specified configuration
    # The group name is unique to avoid conflicts with other jobs
    
    print(f"Starting container group {group_name} for job {job_id}...")
    
    client.container_groups.begin_create_or_update(
        ACR_RESOURCE_GROUP,
        group_name,
        group
    )