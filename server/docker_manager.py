import docker
import os
import shutil
import tempfile
from server.generator import generate_model_app

client = docker.from_env()

# 🔧 Task-specific dependencies
TASK_DEPENDENCIES = {
    # Computer Vision
    "image-classification": ["pillow", "torchvision"],
    "object-detection": ["pillow", "torchvision"],
    "image-segmentation": ["pillow", "torchvision"],
    "depth-estimation": ["pillow", "torchvision"],
    "zero-shot-image-classification": ["pillow", "torchvision"],

    # Generative
    "text-to-image": ["diffusers", "accelerate", "pillow"],
    "image-to-image": ["diffusers", "pillow"],

    # Audio
    "automatic-speech-recognition": ["torchaudio"],

    # Video (basic support)
    "video-classification": ["opencv-python", "torchvision"],
}

# 🧠 Base dependencies (always installed)
BASE_DEPENDENCIES = [
    "fastapi",
    "uvicorn",
    "transformers",
    "torch --index-url https://download.pytorch.org/whl/cpu"
]

# 🐳 Dockerfile template
DOCKERFILE = """FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 -r requirements.txt

COPY main.py .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def resolve_dependencies(task: str):
    extra = TASK_DEPENDENCIES.get(task, [])
    return BASE_DEPENDENCIES + extra


def build_and_run(model_id: str, task: str, port: int) -> str:
    model_slug = model_id.replace("/", "-")
    image_tag = f"modelup-{model_slug}"
    container_name = f"modelup-{model_slug}"

    build_dir = tempfile.mkdtemp()

    try:
        # 🧩 Generate model-specific FastAPI app
        generate_model_app(model_id, task, build_dir)

        # 📦 Resolve dependencies dynamically
        deps = resolve_dependencies(task)

        # 📝 Write requirements.txt
        with open(os.path.join(build_dir, "requirements.txt"), "w") as f:
            f.write("\n".join(deps))

        # 🐳 Write Dockerfile
        with open(os.path.join(build_dir, "Dockerfile"), "w") as f:
            f.write(DOCKERFILE)

        # 🔨 Build image
        image, logs = client.images.build(
            path=build_dir,
            tag=image_tag,
            rm=True
        )

        for log in logs:
            if "stream" in log:
                print(log["stream"], end="")

        # 🧹 Remove existing container if exists (prevents name conflict)
        try:
            existing = client.containers.get(container_name)
            existing.stop()
            existing.remove()
        except docker.errors.NotFound:
            pass

        # 🚀 Run container
        container = client.containers.run(
            image_tag,
            detach=True,
            ports={"8000/tcp": port},
            name=container_name,
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