import os
from slacker import Slacker
from app_image_generator.plugins.base import BasePlugin


class SlackPlugin(BasePlugin):
    def __init__(self):
        self.slacker = Slacker(os.environ.get("SLACK_TOKEN"))

    def build_succeeded(self, output):
        self.slacker.chat.post_message('#dev', 'New images available:', username='app-image-generator', attachments=[
            {
                "fields": [
                    {
                        "title": image_name,
                        "value": image_id,
                        "short": True
                    } for image_name, image_id in self.get_images_from_output(output).items()
                ],
            }
        ])

    def build_failed(self, output):
        self.slacker.chat.post_message('#dev', 'Build failed!!!!', username='app-image-generator', attachments=[
            {
                "fields": [
                    {
                        "title": image_name,
                        "value": image_id,
                        "short": True
                    } for image_name, image_id in self.get_images_from_output(output).items()
                ],
                "color": "#F35A00"
            }
        ])
