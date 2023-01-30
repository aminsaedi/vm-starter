import typer

from helper.deployer import Deployer

app = typer.Typer()

@app.command()
def deploy():
    deployer = Deployer()
    deployer.deploy()


@app.command()
def destroy():
    deployer = Deployer()
    deployer.destroy()

if __name__ == "__main__":
    app()
