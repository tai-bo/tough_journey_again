from google.cloud.storage import Client


def get_storage_client() -> Client:
  return Client()
