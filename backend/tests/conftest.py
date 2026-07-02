import os
import sys

# backend/app is a plain (non-installed) package -- make sure `backend/` is on
# sys.path regardless of where pytest's cwd/rootdir ends up, so `import app.main`
# works the same way it does when uvicorn runs from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
