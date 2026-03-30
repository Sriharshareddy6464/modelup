import docker
import os
import shutil
import tempfile
from server.generator import generate_model_app

client = docker.from_env()

REQUIREMENTS = "fastapi\nuvicorn\ntransformers\ntorch --index-url https://download.pytorch.org/whl/cpu\n"

DOCKERFILE = """FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 -r requirements.txt
COPY main.py .
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

def build_and_run(model_id: str, task: str, port: int) -> str:
    model_slug = model_id.replace("/", "-")
    image_tag = f"modelup-{model_slug}"
    build_dir = tempfile.mkdtemp()
    try:
        generate_model_app(model_id, task, build_dir)
        with open(os.path.join(build_dir, "Dockerfile"), "w") as f:
            f.write(DOCKERFILE)
        with open(os.path.join(build_dir, "requirements.txt"), "w") as f:
            f.write(REQUIREMENTS)
        image, logs = client.images.build(path=build_dir, tag=image_tag, rm=True)
        for log in logs:
            if 'stream' in log:
                print(log['stream'], end='')
        container = client.containers.run(
            image_tag,
            detach=True,
            ports={"8000/tcp": port},
            name=f"modelup-{model_slug}",
            restart_policy={"Name": "unless-stopped"}
        )
        return container.id
    finally:
        shutil.rmtree(build_dir)

def stop_and_remove(model_id: str):
    model_slug = model_id.replace("/", "-")
    image_tag = f"modelup-{model_slug}"
    container_name = f"modelup-{model_slug}"
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        pass
    try:
        client.images.remove(image_tag, force=True)
    except docker.errors.ImageNotFound:
        pass