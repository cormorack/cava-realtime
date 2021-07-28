import typer
from cava_realtime.producer import main as producer
app = typer.Typer()
app.add_typer(producer.app, name="producer")
