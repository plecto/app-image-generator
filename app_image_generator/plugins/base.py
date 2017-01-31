import re


class BasePlugin(object):

    def get_images_from_output(self, output):
        return dict(re.findall(b"\-\-> (\w+): [\w ]+:\n\n[\w-]+: ([\w-]+)", output))

    def build_succeeded(self, output):
        pass

    def build_failed(self, output):
        pass
