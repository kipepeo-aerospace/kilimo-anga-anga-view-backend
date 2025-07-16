from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os


def init_cosmos(app):
    # Initialize Cosmos client
    cosmos_conn_string = app.state.azure_cosmos_connection_string
    client = CosmosClient.from_connection_string(cosmos_conn_string)

    cosmos_db_name = app.state.azure_cosmos_db_name
    database = client.get_database_client(cosmos_db_name)

    # get containers from database and connect them tp app
    app.state.users_container = database.get_container_client("users")
    app.state.farms_container = database.get_container_client("farms")
    app.state.images_container = database.get_container_client("images")
    app.state.jobs_container = database.get_container_client("jobs")
