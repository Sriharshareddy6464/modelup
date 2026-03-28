from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from server.docker_manager import build_and_run, stop_and_remove
from server.port_manager import find_free_port
from server.nginx_manager import add_route, remove_route

app = FastAPI()

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")

def load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return json.load(f)

def save_registry(data: dict):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=2)


class DeployRequest(BaseModel):
    model_id: str
    task: str


@app.post("/deploy")
def deploy(req: DeployRequest):
    registry = load_registry()
    model_slug = req.model_id.replace("/", "-")

    if model_slug in registry:
        raise HTTPException(status_code=400, detail="Model already deployed")

    port = find_free_port()
    container_id = build_and_run(req.model_id, req.task, port)
    add_route(model_slug, port)

    registry[model_slug] = {
        "model_id": req.model_id,
        "task": req.task,
        "port": port,
        "container_id": container_id,
        "status": "running"
    }
    save_registry(registry)

    return {
        "model_slug": model_slug,
        "port": port,
        "endpoint": f"/models/{model_slug}/predict"
    }


@app.delete("/deploy/{model_slug}")
def destroy(model_slug: str):
    registry = load_registry()

    if model_slug not in registry:
        raise HTTPException(status_code=404, detail="Model not found")

    model_id = registry[model_slug]["model_id"]
    stop_and_remove(model_id)
    remove_route(model_slug)

    del registry[model_slug]
    save_registry(registry)

    return {"destroyed": model_slug}


@app.get("/list")
def list_models():
    return load_registry()


@app.get("/info/{model_slug}")
def info(model_slug: str):
    registry = load_registry()
    if model_slug not in registry:
        raise HTTPException(status_code=404, detail="Model not found")
    return registry[model_slug]


@app.get("/status")
def status():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)