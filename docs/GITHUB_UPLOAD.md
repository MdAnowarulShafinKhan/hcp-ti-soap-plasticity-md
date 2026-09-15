# GitHub upload checklist

1. Extract the ZIP locally.
2. Create a new empty GitHub repository, e.g. `hcp-ti-soap-plasticity-md`.
3. Upload the **contents of the extracted repository folder**, not the ZIP itself.
4. Keep the included `.gitignore` file.
5. Before committing, make sure no `trajectory.lammpstrj`, restart binaries, or `soap_local_samples.npz` files were added.
6. Confirm the README renders the figures correctly.
7. Confirm the largest committed file is below GitHub's normal single-file limits (all files in this prepared package are below 25 MiB, so they can also be uploaded through the browser).

Command-line alternative:

```bash
git init
git add .
git commit -m "Add HCP Ti MD + PTM/SOAP plasticity project"
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```
