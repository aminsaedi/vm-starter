import re
import os
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


class RepositoryHelper:
    backend_versions = []
    frontend_versions = []

    major_versions = []

    __frontend_repo = "git@bitbucket.org:employeeportal/frontend.git"
    __backend_repo = "git@bitbucket.org:employeeportal/backend.git"

    def __init__(self):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(description="Initializing...", total=None)
            # self.backend_versions = [
            #    "v1.0.0", "v1.0.1", "v1.0.2", "v1.1.0", "v1.1.2", "v2.0.0", "v2.0.1", "v3.0.0"]
            # self.frontend_versions = [
            #    "v1.0.0", "v1.1.2", "v1.3.4",  "v2.0.0", "v2.0.4"]
            self.backend_versions = self.__read_repo_tags(self.__backend_repo)
            self.frontend_versions = self.__read_repo_tags(
                self.__frontend_repo)
            self.__get_available_versions()

    def __intersection(self, list1, list2):
        return list(set(list1) & set(list2))

    def __read_repo_tags(self, repository: str):
        command = f"""git ls-remote --tags {repository} | egrep -o "tags\/.*}}$" | sed 's/tags\///' | sed 's/\^{{}}//'"""
        output = os.popen(command).read()
        versions = []
        for i in output.split("\n"):
            # 6 is the minimum length of a version tag (v1.0.0)
            if len(i) >= 6:
                versions.append(i)
        return versions

    def __get_available_versions(self):
        backend_majors = [int(value.split(".")[0][1:])
                          for value in self.backend_versions]
        frontend_majors = [int(value.split(".")[0][1:])
                           for value in self.frontend_versions]
        intersect = self.__intersection(backend_majors, frontend_majors)
        self.major_versions = intersect

    def __get_latest_version(self, ver: int, all_versions: list) -> str:
        return next(x for x in all_versions[::-1] if bool(re.search(f"(v|V){ver}\.+\d+\.\d+", x)))

    def __get_combined_formatted_label(self, ver: int) -> str:
        latest_backend = self.__get_latest_version(ver, self.backend_versions)
        latest_frontend = self.__get_latest_version(
            ver, self.frontend_versions)
        return "backend ver: {backend} - frontend ver: {frontend}".format(backend=latest_backend, frontend=latest_frontend)

    def get_choieses(self):
        return [(self.__get_combined_formatted_label(x), x) for x in self.major_versions]

    def download(self, ver: int):

        if ver not in self.major_versions:
            raise Exception("Invalid version")

        latest_backend = self.__get_latest_version(ver, self.backend_versions)
        latest_frontend = self.__get_latest_version(
            ver, self.frontend_versions)
        commands = {
            "backend": f"git clone -q --depth 1 --branch {latest_backend} {self.__backend_repo} > /dev/null 2>&1",
            "frontend": f"git clone -q --depth 1 --branch {latest_frontend} {self.__frontend_repo} > /dev/null 2>&1"
        }
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            progress.add_task(
                description="Downloading repositories...", total=None)
            os.system("rm -rf backend")
            os.system("rm -rf frontend")
            os.system(commands["backend"])
            os.system(commands["frontend"])
            os.system("cp ./backend.env backend/.env")
            os.system("cp ./frontend.env frontend/.env")


class DockerHelper:

    def __init__(self):
        if not os.path.exists(os.path.expanduser("docker-compose.yml")):
            raise Exception("docker-compose.yml not found")

        if not os.path.exists(os.path.expanduser("./database")):
            os.system("mkdir ./database")

        # check if docker is running
        if os.system("docker info > /dev/null") != 0:
            raise Exception("Docker not running")

        # check if docker-compose is installed
        if os.system("docker-compose --version > /dev/null") != 0:
            raise Exception("Docker-compose not installed")

    def up(self, new_build: bool = False):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            progress.add_task(
                description="Starting containers...", total=None)
            os.system(
                f"docker-compose up -d {'--build' if new_build else ''} > /dev/null 2>&1")
        print("Containers started successfully")

    def down(self):
        os.system("docker-compose down > /dev/null 2>&1")

    def prune_images(self):
        os.system("docker rmi $(docker images -q) > /dev/null 2>&1")

    def migration_fixer(self):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            progress.add_task(
                description="Running migration fixes...", total=None)
            os.system(
                """docker exec -it compose-database-1 /usr/bin/mongosh "mongodb://root:example@database:27017/employeeDomain?directConnection=true&authSource=admin&replicaSet=replicaset&retryWrites=true" --eval 'db.groups.updateMany({systemType:"RETIRED"},{$set:{systemType:"RETIREE"}})' > /dev/null""")
            os.system(
                """docker exec -it compose-database-1 /usr/bin/mongosh "mongodb://root:example@database:27017/employeeDomain?directConnection=true&authSource=admin&replicaSet=replicaset&retryWrites=true" --eval 'db.groups.updateMany({systemType:"TEMP_LAY_OFF"},{$set:{systemType:"TEMP_LAID_OFF"}})' > /dev/null""")

    def is_dump_exists(self) -> bool:
        return os.path.exists(os.path.expanduser("~/dump"))

    def restore_data(self):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            progress.add_task(
                description="Restoring data from ~/dump ...", total=None)
            os.system(
                """docker cp ~/dump compose-database-1:/dump""")
            os.system(
                """docker exec -it compose-database-1 /usr/bin/mongorestore --username root --password example --authenticationDatabase admin --db employeeDomain --drop dump/""")

    def clean_work_directory(self):
        os.system("rm -rf ./backend")
        os.system("rm -rf ./frontend")
