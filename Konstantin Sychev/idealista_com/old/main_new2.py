import json

import requests

TOKEN_FILE = "token.json"
DATA_FILE = "properties_72.json"
PROPERTY_API_URL = "https://allproperty.ai/wp-json/wp/v2/properties"

# Load the token
with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
    token_data = json.load(token_file)
    token = token_data.get("token")

# Load the property data
with open(DATA_FILE, "r", encoding="utf-8") as data_file:
    properties_data = json.load(data_file)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def prepare_payload(property_data):
    """
    Prepares the payload for importing property data into WordPress.
    """
    payload = {
        "title": {"rendered": property_data.get("title", "Untitled Property")},
        "status": property_data.get("status", "publish"),
        "meta": {
            "price": property_data["property_meta"].get("fave_property_price", [""])[0],
            "size": property_data["property_meta"].get("fave_property_size", [""])[0],
            "bedrooms": property_data["property_meta"].get(
                "fave_property_bedrooms", [""]
            )[0],
            "bathrooms": property_data["property_meta"].get(
                "fave_property_bathrooms", [""]
            )[0],
            "garage": property_data["property_meta"].get("fave_property_garage", [""])[
                0
            ],
        },
        "content": property_data["content"]["rendered"],
        "property_type": property_data.get("property_type", []),
        "property_status": property_data.get("property_status", []),
        "property_feature": property_data.get("property_feature", []),
        "property_label": property_data.get("property_label", []),
        "property_country": property_data.get("property_country", []),
        "property_state": property_data.get("property_state", []),
        "property_city": property_data.get("property_city", []),
        "property_area": property_data.get("property_area", []),
    }

    # Handle additional fields, e.g., images, videos, and features
    images = property_data["property_meta"].get("fave_property_images", [])
    if images:
        payload["meta"]["images"] = images

    additional_features = property_data["property_meta"].get("additional_features", [])
    if additional_features:
        payload["meta"]["additional_features"] = additional_features

    return payload


def upload_properties():
    """
    Uploads properties to WordPress using the prepared payload.
    """
    for property_data in properties_data:
        payload = prepare_payload(property_data)
        response = requests.post(PROPERTY_API_URL, headers=headers, json=payload)

        if response.status_code == 201:
            print(
                f"Property '{property_data['title']['rendered']}' successfully uploaded."
            )
        else:
            print(
                f"Failed to upload property '{property_data['title']['rendered']}': {response.text}"
            )


if __name__ == "__main__":
    upload_properties()
