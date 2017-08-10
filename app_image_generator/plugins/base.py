import re


class BasePlugin(object):

    def get_images_from_output(self, output):
        return {k.decode("utf-8"): i.decode("utf-8") for k, i in re.findall(b"\-\-> (\w+): [\w ]+:\n\n[\w-]+: ([\w-]+)", output)}

    def build_succeeded(self, app, output):
        pass

    def build_failed(self, app, output):
        pass
