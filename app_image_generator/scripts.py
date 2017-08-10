from __future__ import print_function
import json
from subprocess import Popen, PIPE, STDOUT
import pprint
from app_image_generator.deployment import Deployment


def run(base_ami, version, revision, git_revision, deployment_file, app, base_ami_name=None, build_job=None,
        build_number=None, files=None, amis=None, verbosity=0, noop=False, install_command=None,
        extra_account_ids=None, builder_type=None, plugins=None, **kwargs):
    if 'packer_bin' in kwargs:
        packer_bin = kwargs.pop('packer_bin')
    else:
        packer_bin = "packer"
    if not files:
        files = []
    deployment = Deployment(base_ami, version, revision, git_revision, deployment_file, app, base_ami_name, build_job,
                            build_number, files=files, amis=amis, install_command=install_command,
                            extra_account_ids=extra_account_ids, instance_type=kwargs.get('build_instance_type'),
                            builder_type=builder_type
    )
    packer_input = deployment.packer_json()
    if verbosity and verbosity > 0:
        print("PACKER JSON")
        print("===========")
        pprint.pprint(json.loads(packer_input))
        print("===========")
    packer_cmd = [packer_bin, "build", "-"]
    if not noop:
        p = Popen(packer_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        output = b''
        try:
            p.stdin.write(str.encode(packer_input))
            p.stdin.close()
            for line in iter(p.stdout.readline, b''):
                output += line
                try:
                    print(line, flush=True)  # Don't add a line break, as it's already provided by the output
                except TypeError:  # Python<3.5
                    print(line)
            p.stdout.close()
            return_code = p.wait()

        except KeyboardInterrupt:
            p.kill()
            return_code = 1

        for plugin in plugins:
            if return_code == 0:
                plugin.build_succeeded(app, output)
            else:
                plugin.build_failed(app, output)

        return return_code
    else:
        print("NOOP: ",  " ".join(packer_cmd))
