
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
import os
import inquirer

from .helper import RepositoryHelper, DockerHelper


class Deployer:
    def __init__(self):
        return

    def deploy(self):
        repository = RepositoryHelper()
        versions = repository.get_choieses()

        questions = [
            inquirer.List('version',
                          message="Which version do you want to deploy?",
                          choices=versions,
                          ),
        ]

        answers = inquirer.prompt(questions)
        selected_version = answers['version']

        print(f"Deploying version {selected_version} ...")

        repository.download(selected_version)

        docker = DockerHelper()

        should_use_new_build = typer.confirm(
            "Do you want to use new build?", default=True)

        docker.down()
        docker.up(new_build=should_use_new_build)

        run_migration_fixes = typer.confirm(
            "Do you want to run migration fixes?", default=True)
        if run_migration_fixes:
            docker.migration_fixer()

        if docker.is_dump_exists():
            print("Database dump directory exists...")
            should_restore_data = typer.confirm(
                "Do you want to restore data using dum data in ~/dump?", default=False)
            if should_restore_data:
                docker.restore_data()

        print("Your application is ready to use.")

        return

    def destroy(self):

        typer.confirm(
            "Are you sure you want to destroy docker containers?", abort=True)
        docker = DockerHelper()
        docker.down()
        print("Docker containers are destroyed.")

        delete_images = typer.confirm(
            "Do you want to delete docker images?", default=True)
        if delete_images:
            docker.prune_images()
            print("Docker images are deleted.")

        clean_work_directory = typer.confirm(
            "Do you want to clean work directory?", default=True)
        if clean_work_directory:
            docker.clean_work_directory()
