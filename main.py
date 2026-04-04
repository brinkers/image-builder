import logging
import time
import requests
import dotenv
import os
import json
import image_builder
import argparse
import sys


def readargs():
    # Create the parser
    parser = argparse.ArgumentParser(description="Start image builder.")

    parser.add_argument(
        "distribution",
        choices=["rhel-8", "rhel-9", "rhel-10"],
        help="distribution to use for the image (e.g., rhel-9)",
    )

    parser.add_argument("template", type=str, help="Template file to use for the image")

    args = parser.parse_args()

    return (args.distribution, args.template)


def delete_old_composes(api_client, blueprint_id):
    composes = api_client.get_composes_for_blueprint(blueprint_id)
    for compose in composes["data"]:
        compose_status = api_client.get_compose_status(compose["id"])
        if compose_status["image_status"]["status"] in ["success", "failure"]:
            api_client.delete_compose(compose["id"])
            logging.info(f"Deleted old compose with ID: {compose['id']}")   


def main(distribution, template):
    logger = logging.getLogger(__name__)
    logger.info("Starting the image builder script.")
    dotenv.load_dotenv()
    client = os.environ["ACCOUNT"]
    secret = os.environ["SECRET"]
    if not client or not secret:
        raise ValueError("ACCOUNT and SECRET environment variables must be set.")
    logger.info(
        "Successfully loaded the ACCOUNT and SECRET from environment variables."
    )
    logger.info(f"Using distribution: {distribution} and template: {template}")

    with open(template, "r") as f:
        blueprint_content = f.read()

    blueprint_object = json.loads(blueprint_content)

    api_client = image_builder.ImageBuilderClient(
        client_id=client, client_secret=secret, dumpResponse=False
    )

    blueprints = api_client.get_blueprints()

    
    bp = next((bp for bp in blueprints["data"] if bp["name"] == "StandardImage"), None)

    if not bp:
        logger.error("Blueprint 'StandardImage' not found.")
        raise Exception("Blueprint 'StandardImage' not found.")

    logger.info("Found the 'StandardImage' blueprint.")

    current_composes = api_client.get_composes_for_blueprint(bp["id"])

    if current_composes:
        
        logger.info(f"Number of existing composes for blueprint: {len(current_composes['data'])}")
        delete_old_composes(api_client, bp["id"])

    logger.info(f"Starting compose, ID: {bp['id']}")  
    payload = { "image_types": ["azure", "aws"] }

    api_client.enable_http_debug()
    
    compose = api_client.create_compose_from_blueprint(bp["id"], data=payload)

    id = compose["id"]

    # id = api_client.create_compose(blueprint_object)
    # logger.info(f"Started compose, ID: {id}")
    status = api_client.get_compose_status(id)
    logger.info(f"Initial compose status: {status['image_status']['status']}")

    sleep_time = 30
    while status['image_status']['status'] not in ["success", "failure"]:
        logger.info(f"Compose status: {status['image_status']['status']}. Checking again in {sleep_time} seconds...")
        time.sleep(sleep_time)
        status = api_client.get_compose_status(id)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # Set minimum log level
        format="%(asctime)s - %(levelname)s - %(message)s",  # Include time, level, and message
        datefmt="%Y-%m-%d %H:%M:%S",  # Custom time format
    )
    distribution, template = readargs()
    main(distribution, template)


# status = api_client.get_compose_status(id)
# logger.info(f"Initial compose status: {status['image_status']['status']}")


# sleep_time = 30
# while status['image_status']['status'] not in ["success", "failure"]:
#     logger.info(f"Compose status: {status['image_status']['status']}. Checking again in {sleep_time} seconds...")
#     time.sleep(sleep_time)
#     status = api_client.get_compose_status(id)

# logger.info(f"Final compose status: {status['image_status']['status']}")

# print(json.dumps(status, indent=4))
