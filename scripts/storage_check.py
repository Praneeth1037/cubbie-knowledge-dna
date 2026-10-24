"""Storage preflight, including an explicit temporary-mode result on persistence failure."""
import json
try:
    from .diagnose import DiagnosticService
except ImportError:
    from diagnose import DiagnosticService

if __name__ == "__main__":
    print(json.dumps(DiagnosticService().handle({"action": "storage-check"})))
