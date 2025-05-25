# --- agents/plugin_loader.py ---
import importlib.util
import os
from langchain.schema.runnable import RunnableLambda

PLUGIN_DIR = "agents/plugins"


def load_plugins():
    plugins = []
    for fname in os.listdir(PLUGIN_DIR):
        if fname.endswith(".py"):
            spec = importlib.util.spec_from_file_location(
                fname[:-3], os.path.join(PLUGIN_DIR, fname))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            plugins.append(mod)
    return plugins
