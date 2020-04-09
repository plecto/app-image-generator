import argparse
from app_image_generator.plugins.slack import SlackPlugin
from app_image_generator.plugins.spinnaker import SpinnakerPlugin
from app_image_generator.scripts import run
from app_image_generator.startup import upstart_script_template, systemd_script_template
import sys

print(" ".join(sys.argv))

parser = argparse.ArgumentParser()
parser.add_argument("base-ami", help="AMI to build on top of, in the format ami-XXXXX")
parser.add_argument("base-ami-name", help="Name of the base ami")
parser.add_argument("base-ami-version", help="Version of the bae ami")
parser.add_argument("package-name", help="Name of the application you want to package")
parser.add_argument("package-version", help="Version of the application, such as 1.2.3")
parser.add_argument("package-revision", help="Revision of the build, usually 1", default='1')
parser.add_argument("package-file", help="A tar.gz with the application code to be deployed")
parser.add_argument("package-source-revision", help="The revision of the code from e.g. GIT")
parser.add_argument("build-job", help="The name of the build job")
parser.add_argument("build-number", help="The build number")
parser.add_argument("-v", "--verbosity", action="count", help="increase output verbosity")
parser.add_argument("-n", "--noop", help="Don't run packer, but print the command it would have run", action='store_true', default=False)
parser.add_argument("--packer-binary", help="The path to packer. Defaults to 'packer'", default="packer")
parser.add_argument("--install-command", help="Command to install requirements. Defaults to 'pip install -r requirements.txt'", default="pip install -r requirements.txt")
parser.add_argument("-s", "--script", help="Script to run with upstart, e.g. python manage.py runserver", action='append')
parser.add_argument("-d", "--deployment-name", help="Name of the environment, is paired with scripts", action='append')
parser.add_argument("-a", "--aws-account-id", help="AWS Account ids for extra users that have read-only access", action='append')
parser.add_argument("--build-instance-type", help="The AWS instance type used for building the image", default='t1.micro')
parser.add_argument('--single-image', dest='single_image', action='store_true', default=False, help="Rather than generating an image per script, put all scripts in the same image")
parser.add_argument("--builder-type", help="Advanced: Choose between amazon-ebs and amazon-chroot", default='amazon-ebs')
parser.add_argument("-p", "--plugins", help="Plugins to execute on finish. [slack]", action='append')


def main():
    args = parser.parse_args()

    run_kwargs = dict(args._get_kwargs())

    if len(run_kwargs['script']) > 1 and len(run_kwargs['deployment_name']) != len(run_kwargs['script']):
        print("Please provide the same number of deployment name and scripts, when using multiple scripts")
        exit(1)
    elif len(run_kwargs['script']) == 0:
        print("Please provide at least one script")
        exit(1)

    plugins = []
    if run_kwargs['plugins']:
        for plugin in run_kwargs['plugins']:
            if plugin == 'slack':
                plugins.append(SlackPlugin())
            elif plugin == 'spinnaker':
                plugins.append(SpinnakerPlugin())

    kwargs = dict(
        script=run_kwargs['script'],
        upstart_name=run_kwargs['package-name'],
        base_ami=run_kwargs['base-ami'],
        version=run_kwargs['package-version'],
        revision=run_kwargs['package-revision'],
        git_revision=run_kwargs['package-source-revision'],
        deployment_file=run_kwargs['package-file'],
        app=run_kwargs['package-name'],
        base_ami_name=run_kwargs['base-ami-name'],
        build_job=run_kwargs['build-job'],
        build_number=run_kwargs['build-number'],
        verbosity=run_kwargs['verbosity'],
        noop=run_kwargs['noop'],
        packer_bin=run_kwargs['packer_binary'],
        install_command=run_kwargs['install_command'],
        extra_account_ids=run_kwargs['aws_account_id'],
        build_instance_type=run_kwargs['build_instance_type'],
        builder_type=run_kwargs['builder_type'],
        plugins=plugins
    )
    if len(run_kwargs['script']) > 1:  # Multiple upstart-scripts
        env_script_dict = zip(run_kwargs['deployment_name'], run_kwargs['script'])
        if run_kwargs['single_image']:  # Put all upstart-files in the same AMI
            run(files=[
                {
                    'content': upstart_script_template(f, "-".join([kwargs['app'], environment]), kwargs.get('maintainer', 'Unknown')),
                    'filename': "/etc/init/%s.conf" % "-".join([kwargs['app'], environment]),
                }
                for environment, f in env_script_dict],
                **kwargs
            )
        else:  # Put all upstart-files in separate AMIs
            kwargs['amis'] = [deployment for deployment, f in env_script_dict]
            run(files=[
                {
                    'content': upstart_script_template(f, "-".join([kwargs['app'], environment]), kwargs.get('maintainer', 'Unknown')),
                    'filename': "/etc/init/%s.conf" % "-".join([kwargs['app'], environment]),
                    'deployment': environment,
                }
                for environment, f in env_script_dict],
                **kwargs
            )
    else:  # Single script and single AMI!
        return_code = run(files=[
            {
                'content': systemd_script_template(kwargs['script'][0], kwargs['app'], kwargs.get('maintainer', 'Unknown')),
                'filename': "/etc/systemd/system/%s.service" % kwargs['app'],
                'systemd_service_name': kwargs['app'],
            }
        ], **kwargs)
        exit(return_code)
