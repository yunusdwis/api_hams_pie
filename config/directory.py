import os
from dotenv import load_dotenv

load_dotenv()

directory = {
    'people': os.getenv('DIR_PEOPLE'),
    'bpjs': os.getenv('DIR_BPJS'),
    'medical_checkup': os.getenv('DIR_MEDICAL_CHECKUP'),
    'skck': os.getenv('DIR_SKCK'),
}