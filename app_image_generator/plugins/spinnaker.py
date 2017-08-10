import json
import os
import requests
from app_image_generator.plugins.base import BasePlugin


class SpinnakerPlugin(BasePlugin):
    """
    Expects the following environment variables:

    SPINNAKER_PIPELINE_APP_URL: http://spinnaker/gate/pipelines/mylittlepony
    SPINNAKER_USER: basicauthuser
    SPINNAKER_PASSWORD: basicauthpw
    """
    def build_succeeded(self, app, output):
        for image_name, image_id in self.get_images_from_output(output).items():
            requests.post(
                "%s/%s" % (os.environ.get("SPINNAKER_PIPELINE_APP_URL"), image_name),
                data=json.dumps({
                    "type": "manual",
                    "parameters": {"prebaked_ami": image_id},
                    "user": "[circle]"}
                ),
                auth=(os.environ.get("SPINNAKER_USER"), os.environ.get("SPINNAKER_PASSWORD")),
                headers={
                    'Content-Type': 'application/json'
                }
            )