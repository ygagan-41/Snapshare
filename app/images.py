import os
from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

private_key = os.getenv("IMAGEKIT_PRIVATE_KEY")
public_key = os.getenv("IMAGEKIT_PUBLIC_KEY")
url_endpoint = os.getenv("IMAGEKIT_URL")

if not private_key:
    raise RuntimeError(
        "IMAGEKIT_PRIVATE_KEY is missing. Add it to your .env file in the project root."
    )

# The installed ImageKit SDK version determines which constructor arguments it accepts.
try:
    imagekit = ImageKit(private_key=private_key, public_key=public_key, url_endpoint=url_endpoint)
except TypeError as exc:
    if "unexpected keyword argument" not in str(exc):
        raise
    imagekit = ImageKit(private_key=private_key)