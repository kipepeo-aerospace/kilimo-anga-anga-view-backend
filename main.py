from fastapi import FastAPI, Path, File, Form, UploadFile
from azure.storage.blob import BlobServiceClient
from azure.core.pipeline.transport import RequestsTransport
import os
from dotenv import load_dotenv
from routes import farms, profile, upload, gallery, process

from fastapi.middleware.cors import CORSMiddleware
from db.cosmos import init_cosmos

##############################################
# Load environment variables
##############################################

load_dotenv()  # Load environment variables from .env file

# Get the connection string securely from the environment
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

if AZURE_STORAGE_CONNECTION_STRING is None:
    raise EnvironmentError("AZURE_STORAGE_CONNECTION_STRING is not set.")


# Create a custom transport with extended timeouts
transport = RequestsTransport(connection_timeout=60, read_timeout=600)

# Initialize the blob service client
blob_service = BlobServiceClient.from_connection_string(
    AZURE_STORAGE_CONNECTION_STRING,
    transport=transport)

################################################
# FastAPI app setup
################################################

origins = [
    "http://localhost:5173",  # frontend dev server
]

######################################################
# Initialize app and add CORS middleware
######################################################
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

####################################################
# Attach env variables to app state
####################################################
app.state.blob_client = blob_service
app.state.raw_images_container = os.getenv("RAW_IMAGES_CONTAINER")
app.state.tiff_container = os.getenv("TIFF_CONTAINER")
app.state.mosaic_container = os.getenv("MOSAIC_CONTAINER")
app.state.indices_container = os.getenv("INDICES_CONTAINER")

# sensitive information
app.state.azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
app.state.account_key = os.getenv("AZURE_CONNECTION_KEY")  
app.state.account_name = blob_service.account_name # this too

app.state.acr_image = os.getenv("ACR_IMAGE")
app.state.acr_registry_server = os.getenv("ACR_REGISTRY_SERVER")
app.state.acr_registry_username = os.getenv("ACR_REGISTRY_USERNAME")
app.state.acr_registry_password = os.getenv("ACR_REGISTRY_PASSWORD")

app.state.azure_subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

app.state.azure_cosmos_connection_string = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
app.state.azure_cosmos_db_name = os.getenv("AZURE_COSMOS_DB_NAME")

####################################################
# Initiazlie our cosmos database
####################################################

init_cosmos(app)


######################################################
# Include routers
######################################################
app.include_router(farms.router,  tags=["Farms"])
app.include_router(profile.router, tags=["Profile"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(gallery.router, tags=["Gallery"])
app.include_router(process.router, tags=["Process"])

