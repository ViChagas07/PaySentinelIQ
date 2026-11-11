import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT_STR = str(SERVICE_ROOT)

if SERVICE_ROOT_STR not in sys.path:
    sys.path.insert(0, SERVICE_ROOT_STR)

for module_name in list(sys.modules):
    if module_name != "app" and not module_name.startswith("app."):
        continue
    module = sys.modules[module_name]
    module_file = getattr(module, "__file__", "") or ""
    if not module_file.startswith(SERVICE_ROOT_STR):
        del sys.modules[module_name]
