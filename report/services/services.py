from fastapi import HTTPException
from jinja2 import Template


def load_description(file_path: str) -> str:
    with open(file_path) as f:
        return f.read()


def check_access(user, permission: str):
    if permission not in user.permissions:
        raise HTTPException(status_code=403, detail=f"Access denied for {permission}")


def jinja_template_generator(path: str):
    with open(path) as f:
        template = Template(f.read())
    return template
