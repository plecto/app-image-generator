import json


class Deployment(object):
    def __init__(self, base_ami, version, revision, git_revision, deployment_file, app, base_ami_name=None, build_job=None,
                build_number=None, files=None, amis=None, install_command=None, extra_account_ids=None,
                instance_type=None, builder_type=None):
        self.base_ami = base_ami
        self.version = version
        self.revision = revision
        self.git_revision = git_revision
        self.deployment_file = deployment_file
        self.app = app
        self.base_ami_name = base_ami_name
        self.build_job = build_job
        self.build_number = build_number
        if not files:
            files = []
        self.files = files
        if not amis:
            amis = ['default']
        self.amis = amis
        if not install_command:
            install_command = "pip install -r requirements.txt"
        self.install_command = install_command
        if not extra_account_ids:
            extra_account_ids = []
        self.extra_account_ids = extra_account_ids
        if not instance_type:
            instance_type = "t1.micro"
        self.instance_type = instance_type
        if not builder_type:
            builder_type = "amazon-ebs"
        self.builder_type = builder_type

    def packer_json(self):
        cfg = {
            'variables': {
                "base_ami": self.base_ami,
                "base_ami_name": "" or self.base_ami_name,
                "version": self.version,
                "revision": self.revision,
                "git_revision": self.git_revision,
                "build_job": "" or self.build_job,
                "build_number": "" or self.build_number,
                "deployment_file": self.deployment_file,
                "app": self.app,
            },
            'builders': [],
            'provisioners': [
                {
                    "type": "file",
                    "source": "{{user `deployment_file`}}",
                    "destination": "/tmp/app.tar.gz"
                },
                {
                  "type": "shell",
                  "inline": [
                      "set -x",
                      "mkdir -p /app/",
                      "cd /app/",
                      "cp /tmp/app.tar.gz .",
                      "tar xvf app.tar.gz",
                      "rm app.tar.gz",
                      self.install_command
                  ],
                  "execute_command": "chmod +x {{ .Path }}; {{ .Vars }} sudo {{ .Path }}",
                }
            ]
        }

        extra_ami_config = {}
        if self.builder_type == "amazon-ebs":
            extra_ami_config.update({
                "instance_type": self.instance_type,
                "ssh_username": "ubuntu",
            })

        for name in self.amis:
            ami_config = {
                "type": self.builder_type,
                "name": name,
                "region": "eu-west-1",
                "source_ami": "{{user `base_ami`}}",
                "ami_users": self.extra_account_ids,

                "ami_name": "%s-{{user `version`}}-{{user `revision`}}-x86_64-{{isotime | clean_ami_name}}" % ("{{user `app`}}" if name == 'default' else "{{user `app`}}_%s" % name),
                "ami_description": "name=%s, arch=x86_64, ancestor_name={{user `base_ami_name`}}, ancestor_id={{user `base_ami`}}, ancestor_version=" % ("{{user `app`}}" if name == 'default' else "{{user `app`}}_%s" % name),
                "tags": {
                  "appversion": "%s-{{user `version`}}-{{user `revision`}}.h{{ user `build_number` }}/{{user `build_job`}}/{{ user `build_number` }}" % ("{{user `app`}}" if name == 'default' else "{{user `app`}}_%s" % name)
                }

            }
            ami_config.update(extra_ami_config)
            cfg['builders'].append(ami_config)

        for file_dict in self.files:
            inlines = [
                "cat > {filename} << EOF\n{content}\nEOF".format(**file_dict)
            ] + ["systemctl enable {systemd_service_name}".format(**file_dict)] if 'systemd_service_name' in file_dict else []
            cfg['provisioners'].append({
                "type": "shell",
                "inline": inlines,
                "execute_command": "chmod +x {{ .Path }}; {{ .Vars }} sudo {{ .Path }}",
                "only": [file_dict.get('deployment', self.amis[0])]
            })

        # Prevent services from running on our builder AMI
        cfg['provisioners'].insert(0, {
            "type": "shell",
            "inline": [
                "echo '#!/bin/sh' > /usr/sbin/policy-rc.d",
                "echo 'exit 101' >> /usr/sbin/policy-rc.d",
                "chmod a+x /usr/sbin/policy-rc.d"
            ],
            "execute_command": "chmod +x {{ .Path }}; {{ .Vars }} sudo {{ .Path }}"
        })
        cfg['provisioners'].append({
            "type": "shell",
            "inline": [
                "rm -f /usr/sbin/policy-rc.d"
            ],
            "execute_command": "chmod +x {{ .Path }}; {{ .Vars }} sudo {{ .Path }}"
        })

        return json.dumps(cfg)
