# FIT Viewer Docker Usage

## Build the Docker image

```bash
docker build -t fit-viewer .
```

## Run the container (mapping port 8501)

```bash
docker run -p 8501:8501 -v $(pwd)/activities:/app/activities fit-viewer
```

- The app will be available at http://localhost:8501
- Your local `activities` folder will be mounted into the container so new .fit files are always available.

---

**Note:**
- You can rebuild and rerun the container as many times as you want.
- If you want to persist changes to the code, edit files on your host and rebuild the image.
- Pushes to main will redeploy the app
- Syncing new files from garmin: 
  - `winpy bin/sync-activities`