import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GCP_PROJECT_ID  = os.getenv("GCP_PROJECT_ID", "")
    VULTR_IP        = os.getenv("VULTR_IP", "")
    LOCATION        = os.getenv("GCP_LOCATION", "us-central1")

    @classmethod
    def validate(cls):
        """
        Only GOOGLE_API_KEY is hard-required at runtime.
        GCP_PROJECT_ID and VULTR_IP are infrastructure metadata — nice to have but
        the agent can operate without them, preventing unnecessary startup failures.
        """
        if not cls.GOOGLE_API_KEY:
            raise ValueError("Missing required environment variable: GOOGLE_API_KEY")

config = Config()
