from fastapi import FastAPI, Path, File, Form, UploadFile
from azure.storage.blob import BlobServiceClient
from azure.core.pipeline.transport import RequestsTransport
import os
from dotenv import load_dotenv
from routes import farms, profile, upload, gallery

from fastapi.middleware.cors import CORSMiddleware

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
# Define container names from environment variables
RAW_IMAGES_CONTAINER = os.environ.get("RAW_IMAGES_CONTAINER")
TIF_CONTAINER = os.environ.get("TIFF_CONTAINER")
MOSAIC_CONTAINER = os.environ.get("MOSAIC_CONTAINER")
INDICES_CONTAINER = os.environ.get("INDICES_CONTAINER")

# retrieve the key

AZURE_CONNECTION_KEY = os.environ.get("AZURE_CONNECTION_KEY")
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
app.state.raw_images_container = RAW_IMAGES_CONTAINER 
app.state.tif_container = TIF_CONTAINER
app.state.mosaic_container = MOSAIC_CONTAINER
app.state.indices_container = INDICES_CONTAINER 
app.state.account_key = AZURE_CONNECTION_KEY
app.state.account_name = blob_service.account_name

######################################################
# Include routers
######################################################
app.include_router(farms.router,  tags=["Farms"])
app.include_router(profile.router, tags=["Profile"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(gallery.router, tags=["Gallery"])