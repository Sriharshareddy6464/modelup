from jinja2 import Environment, FileSystemLoader
import os

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

def generate_model_app(model_id: str, task: str, output_dir: str) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("model_app.py.j2")

    rendered = template.render(model_id=model_id, task=task)

    output_path = os.path.join(output_dir, "main.py")
    with open(output_path, "w") as f:
        f.write(rendered)

    return output_path