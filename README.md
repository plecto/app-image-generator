app-image-generator
=========

Generates AMIs with your application running on it using upstart and packer.

Install
-------

pip install app-image-generator

Usage
-----

Example command

```bash
app-image-generator
  <parent ami> \ # ami-131231312
  <name of parent ami> \  # "my parent ami"
  <ami major version>-<ami minor version> \  # 1-2
  <project name> \  #  "app-image-generator"
  <project version> \  # "1.2"
  <image revision, normally 1> \  # "1"
  <zip file of the app> \  # "app.tar.gz" - should be in current dir or use absolute path
  <git commit id> \  # 5472434e7a996cc3d209fa024adec9f21774589e
  <ci project name> \  # app-image-generator
  <ci build name> \  # 4222
  -d <process type> -s <script to run> \  # -d web- s "python manage.py run_gunicorn -b 0.0.0.0:5000 -w 4"
  -d <next process type> -s <script to run>
  -v  # verbose :-)
```

Speed up pip install
--------------------

Check out [wheelshop](https://github.com/KristianOellegaard/wheelshop#using-with-dynpacker)
