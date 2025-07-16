import typer
import os
import subprocess
from scripts.seed_sample_data import main as seed_main

def run_tests():
    subprocess.run(["pytest"])

def run_type_check():
    subprocess.run(["mypy", "."])

def clear_db():
    db_path = os.getenv("DB_URL", "sqlite:///kg.db").replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed {db_path}")
    else:
        print(f"No DB found at {db_path}")

def reload_plugins():
    os.environ["DEV_MODE"] = "1"
    print("DEV_MODE set. Restart the API to reload plugins.")

app = typer.Typer()

@app.command()
def seed():
    "Seed the KG and vector store with sample data."
    seed_main()

@app.command()
def clear():
    "Clear the KG database."
    clear_db()

@app.command()
def test():
    "Run all tests."
    run_tests()

@app.command()
def typecheck():
    "Run mypy type checks."
    run_type_check()

@app.command()
def reload_plugins_cmd():
    "Enable DEV_MODE for hot plugin reload (restart API after)."
    reload_plugins()

if __name__ == "__main__":
    app()