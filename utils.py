import os
import tempfile
import json
import shutil

def save_uploaded_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name

def list_collections():
    base_path = "collections"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    return [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

def collection_exists(name):
    return os.path.exists(f"collections/{name}")

def create_collection(name):
    path = f"collections/{name}"
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "meta.json"), "w") as f:
        json.dump({"files": []}, f)

def delete_collection(name):
    path = f"collections/{name}"
    if os.path.exists(path):
        shutil.rmtree(path)

def add_file_to_metadata(collection_name, filename):
    meta_path = f"collections/{collection_name}/meta.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
    else:
        meta = {"files": []}
    if filename not in meta["files"]:
        meta["files"].append(filename)
    with open(meta_path, "w") as f:
        json.dump(meta, f)

def get_collection_files(collection_name):
    meta_path = f"collections/{collection_name}/meta.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
        return meta.get("files", [])
    return []
