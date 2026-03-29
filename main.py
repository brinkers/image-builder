import logging
import time
import dotenv
import os
import json

import image_builder
import argparse


def readargs():
    parser = argparse.ArgumentParser(description="Start image builder.")

    parser.add_argument(
        "--distribution",
        required=True,
        choices=["rhel-8", "rhel-9", "rhel-10"],
        help="distribution to use for the image (e.g., rhel-9)",
    )

    parser.add_argument(
        "--template", 
        default="compose_image.json",
        type=str,
        help="Template file to use for the image",
    )

    parser.add_argument(
        "--dontreplace",
        action="store_true",
        help="Dont replace the image details in the template",
    )
    parser.add_argument(
        "--deleteold", action="store_true", help="Delete the old composes first"
    )
    
    parser.add_argument(
        "--ci", action="store_true", help="Running in CI environment (github actions only supported currently)"
    )

    args = parser.parse_args()
    return args


def delete_old_composes(api_client):
    composes = api_client.get_composes()
    for compose in composes["data"]:
        compose_status = api_client.get_compose_status(compose["id"])
        if compose_status["image_status"]["status"] in ["success", "failure"]:
            logging.info(f"Deleting old compose with ID: {compose['id']}")
            api_client.delete_compose(compose["id"])


def build_image(api_client, distribution, template, dont_replace):
    logger = logging.getLogger(__name__)

    logger.info(f"Using distribution: {distribution} and template: {template}")
    with open(template, "r") as f:
        compose_json = f.read()

    compose = json.loads(compose_json)

    if not dont_replace:
        logger.info("Replacing image details in the template.")
        compose["distribution"] = distribution
        compose["image_name"] = f"standard-image-{distribution}"
        compose["image_description"] = (
            f"Standard image for {distribution} built {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    logger.info(f"Starting compose")
    id = api_client.create_compose(compose)
    logger.info(f"Compose id {id}")

    status = api_client.get_compose_status(id)
    sleep_time = 30
    while status["image_status"]["status"] not in ["success", "failure"]:
        logger.info(
            f"Compose status: {status['image_status']['status']}. Checking again in {sleep_time} seconds..."
        )
        time.sleep(sleep_time)
        status = api_client.get_compose_status(id)

    logger.info(
        f"Compose finished with status {status['image_status']['status']}"
    )
    return (id, status['image_status']['upload_status']['options']['url'])

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
  
    dotenv.load_dotenv()

    args = readargs()
    client = os.environ["REDHAT_CONSOLE_ACCOUNT"]
    secret = os.environ["REDHAT_CONSOLE_SECRET"]
    
    if not client or not secret:
        raise ValueError(
            "REDHAT_CONSOLE_ACCOUNT and REDHAT_CONSOLE_SECRET environment variables must be set."
        )

    api_client = image_builder.ImageBuilderClient(
        client_id=client, client_secret=secret, dumpResponse=False
    )

    if args.deleteold:
        delete_old_composes(api_client)

    id, url = build_image(api_client, args.distribution, args.template, args.dontreplace)
    logger.info(f"Image available at {url}")

    if args.ci:
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            logger.info("Running in CI environment, setting variables in GITHUB_OUTPUT")
            with open(github_output, "a") as f:
                f.write(f"id={id}\n")
                f.write(f"url={url}\n")

    logger.info("Image builder finished")
