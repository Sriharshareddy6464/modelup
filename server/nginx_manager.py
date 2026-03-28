import os
import subprocess

NGINX_CONF_DIR = "/etc/nginx/conf.d"

def add_route(model_slug: str, port: int):
    config = f"""server {{
    listen 80;
    location /models/{model_slug}/ {{
        proxy_pass http://localhost:{port}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
    conf_path = os.path.join(NGINX_CONF_DIR, f"modelup-{model_slug}.conf")
    with open(conf_path, "w") as f:
        f.write(config)

    subprocess.run(["sudo", "nginx", "-s", "reload"], check=True)


def remove_route(model_slug: str):
    conf_path = os.path.join(NGINX_CONF_DIR, f"modelup-{model_slug}.conf")
    if os.path.exists(conf_path):
        os.remove(conf_path)

    subprocess.run(["sudo", "nginx", "-s", "reload"], check=True)