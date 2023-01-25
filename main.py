import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
import os
import sys
from time import sleep
from enum import Enum
import inquirer


app = typer.Typer()


class AvailableRepositories(str, Enum):
    frontend = "frontend"
    backend = "backend"


def get_repository_url(repository: AvailableRepositories):
    return f"git@bitbucket.org:employeeportal/{repository}.git"


def repository_downloader(repository: AvailableRepositories, version: str):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Cloning the frontend repository ...", total=None)
        os.system("rm -rf " + repository)
        command = "git clone -q --depth 1 --branch " + version + \
            " " + get_repository_url(repository) + " > /dev/null 2>&1"
        os.system(command)
    print(f"Cloned {repository} repository.")


def get_available_versions(repository: AvailableRepositories):
    # run the command and get the output
    command = f"""git ls-remote --tags {get_repository_url(repository)} | egrep -o "tags\/.*}}$" | sed 's/tags\///' | sed 's/\^{{}}//'"""
    output = os.popen(command).read()
    versions = []
    for i in output.split("\n"):
        if len(i) > 0:
            versions.append(i)
    return versions


def migration_fixer():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Running migration fixes...", total=None)
        os.system(
            """docker exec -it compose-database-1 /usr/bin/mongosh "mongodb://root:example@database:27017/employeeDomain?directConnection=true&authSource=admin&replicaSet=replicaset&retryWrites=true" --eval 'db.groups.updateMany({systemType:"RETIRED"},{$set:{systemType:"RETIREE"}})' > /dev/null""")
        os.system(
            """docker exec -it compose-database-1 /usr/bin/mongosh "mongodb://root:example@database:27017/employeeDomain?directConnection=true&authSource=admin&replicaSet=replicaset&retryWrites=true" --eval 'db.groups.updateMany({systemType:"TEMP_LAY_OFF"},{$set:{systemType:"TEMP_LAID_OFF"}})' > /dev/null""")


@app.command()
def deploy():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Getting data from BitBucket...", total=None)
        frontend_versions = get_available_versions(
            AvailableRepositories.frontend)
        backend_versions = get_available_versions(
            AvailableRepositories.backend)

    versions = list(set(frontend_versions).intersection(backend_versions))
    versions.sort(reverse=True)

    if len(versions) == 0:
        print("No available version found...")
        sys.exit(1)

    selected_version = None
    use_latest = typer.confirm(
        f"Do you want to deploy the latest version ({versions[0]})?", default=True)
    if use_latest:
        selected_version = versions[0]
    else:
        questions = [
            inquirer.List('version',
                          message="Which version do you want to deploy?",
                          choices=versions,
                          ),
        ]

        answers = inquirer.prompt(questions)
        selected_version = answers['version']

    print(f"Deploying version {selected_version} ...")

    repository_downloader(AvailableRepositories.frontend, selected_version)
    repository_downloader(AvailableRepositories.backend, selected_version)

    # check if docker-compose.yml file exists
    if not os.path.exists(os.path.expanduser("docker-compose.yml")):
        print("docker-compose.yml file doesn't exist...")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Starting docker containers ...", total=None)
        os.system("docker-compose down")
        os.system("docker-compose up -d")

    # check if ~/dump directory exists
    if os.path.exists(os.path.expanduser("~/dump")):
        print("Database dump directory exists...")
        should_restore_data = typer.confirm(
            "Do you want to restore data using dum data in ~/dump?", default=False)
        if should_restore_data:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(
                    description="Restoring data from ~/dump ...", total=None)
                os.system("""docker cp ~/dump compose-database-1:/dump""")
                os.system("""docker exec -it compose-database-1 /usr/bin/mongorestore --username root --password example --authenticationDatabase admin --db employeeDomain --drop dump/""")

    run_migration_fixes = typer.confirm(
        "Do you want to restore data using dum data in ~/dump?", default=False)
    if run_migration_fixes:
        migration_fixer()

    print("Your application is ready to use.")


@app.command()
def bye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye {name}")
    else:
        print(f"Bye {name}")


if __name__ == "__main__":
    app()
