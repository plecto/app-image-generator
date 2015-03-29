import json
import sys
from subprocess import Popen, PIPE, STDOUT
import pprint

def upstart_script(script, description, author):
    return """description "%(description)s"
author "%(author)s"

pre-start script
  mkdir -p /var/log/app
  chown -R root /var/log/app

  while [ ! -f "/tmp/envvars" ]; # wait for envvars to be available, before starting up
  do
    sleep 5
    logger -i -t "$UPSTART_JOB" "Waiting 5s for /tmp/envvars to be available..."
  done
  size=`ls -lah /tmp/envvars | awk '{ print $5 }'`
  logger -i -t "$UPSTART_JOB" "Found /tmp/envvars, size: ${size}"


  while [ ! -f "/credentials/settings.yml" ]; # wait for envvars to be available, before starting up
  do
    sleep 5
    logger -i -t "$UPSTART_JOB" "Waiting 5s for /credentials/settings.yml to be available..."
  done
  size=`ls -lah /credentials/settings.yml | awk '{ print $5 }'`
  logger -i -t "$UPSTART_JOB" "Found /credentials/settings.yml, size: ${size}"
end script

start on runlevel [2345]

respawn
respawn limit 1000 1
console log
chdir /app/

script
  logger -i -t "$UPSTART_JOB" "Starting app"
  . /tmp/envvars
  exec %(script)s >> /var/log/app/app.log 2>&1
end script
    """.replace("$", "\$").replace('`', '\`') % {
        'description': description,
        'author': author,
        'script': script,
    }


def packer_json(base_ami, version, revision, git_revision, deployment_file, app, base_ami_name=None, build_job=None,
                build_number=None, files=None, deployments=None, install_command=None, extra_account_ids=None,
                instance_type=None):
    if not extra_account_ids:
        extra_account_ids = []
    if not instance_type:
        instance_type = "t1.micro"
    if not install_command:
        install_command = "pip install -r requirements.txt"
    if not files:
        files = []
    if not deployments:
        deployments = ['amazon-ebs']
    return json.dumps({
      "variables": {
          "base_ami": base_ami,
          "base_ami_name": "" or base_ami_name,
          "version": version,
          "revision": revision,
          "git_revision": git_revision,
          "build_job": "" or build_job,
          "build_number": "" or build_number,
          "deployment_file": deployment_file,
          "app": app,
        },
        "builders": [
        {
            "type": "amazon-ebs",
            "name": name,
            "region": "eu-west-1",
            "source_ami": "{{user `base_ami`}}",
            "ami_users": extra_account_ids,
            "instance_type": instance_type,
            "ssh_username": "ubuntu",

            "ami_name": "%s-{{user `version`}}-{{user `revision`}}-x86_64-{{isotime | clean_ami_name}}" % ("{{user `app`}}" if name == 'amazon-ebs' else "{{user `app`}}_%s" % name),
            "ami_description": "name=%s, arch=x86_64, ancestor_name={{user `base_ami_name`}}, ancestor_id={{user `base_ami`}}, ancestor_version=" % ("{{user `app`}}" if name == 'amazon-ebs' else "{{user `app`}}_%s" % name),
            "tags": {
              "appversion": "%s-{{user `version`}}-{{user `revision`}}.h{{ user `build_number` }}/{{user `build_job`}}/{{ user `build_number` }}" % ("{{user `app`}}" if name == 'amazon-ebs' else "{{user `app`}}_%s" % name)
            }

       } for name in deployments],
        "provisioners": [{
            "type": "file",
            "source": "{{user `deployment_file`}}",
            "destination": "/tmp/app.tar.gz"
        },{
          "type": "shell",
          "inline": [
              "set -x",
              "mkdir -p /app/",
              "cd /app/",
              "cp /tmp/app.tar.gz .",
              "tar xvf app.tar.gz",
              "rm app.tar.gz",
              install_command
          ],
          "execute_command": "chmod +x {{ .Path }}; {{ .Vars }} sudo {{ .Path }}",
        }] + [{
          "type": "shell",
          "inline": ["cat > %(filename)s << EOF\n%(content)s\nEOF" % f],
          "execute_command": "chmod +x {{ .Path }}; {{ .Vars }} sudo {{ .Path }}",
          "only": [f.get('deployment', deployments[0])]
        } for f in files]
    })


def run(base_ami, version, revision, git_revision, deployment_file, app, base_ami_name=None, build_job=None,
        build_number=None, files=None, deployments=None, verbosity=0, noop=False, install_command=None,
        extra_account_ids=None, **kwargs):
    if 'packer_bin' in kwargs:
        packer_bin = kwargs.pop('packer_bin')
    else:
        packer_bin = "packer"
    if not files:
        files = []
    packer_input = packer_json(base_ami, version, revision, git_revision, deployment_file, app, base_ami_name, build_job,
                               build_number, files=files, deployments=deployments, install_command=install_command,
                               extra_account_ids=extra_account_ids, instance_type=kwargs.get('build_instance_type'))
    if verbosity > 0:
        print "PACKER JSON"
        print "==========="
        pprint.pprint(json.loads(packer_input))
        print "==========="
    packer_cmd = [packer_bin, "build", "-"]
    if not noop:
        p = Popen(packer_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        try:
            p.stdin.write(packer_input)
            p.stdin.close()
            output = ''
            for line in iter(p.stdout.readline, b''):
                output += line
                print line,  # Don't add a line break, as it's already provided by the output
            p.stdout.close()
        except KeyboardInterrupt:
            p.kill()
    else:
        print "NOOP: ",  " ".join(packer_cmd)


def run_with_upstart_file(script, upstart_name, *args, **kwargs):
    return run(*args, files=[
        {
            'content': upstart_script(script, upstart_name, kwargs.get('maintainer', 'Unknown')),
            'filename': "/etc/init/%s.conf" % upstart_name
        }
    ], **kwargs)