import subprocess
import os

env = os.environ.copy()

subprocess.Popen(
    """git ls-remote --tags git@bitbucket.org:employeeportal/frontend.git | egrep -o "tags\/.*}$" | sed 's/tags\///' | sed 's/\^{}//'""", env=env, stdout=subprocess.PIPE, shell=True)
