# Releasing Buildozer

How to cut a new buildozer release. Maintainer-facing.

## Version source of truth

`__version__` in [`buildozer/__init__.py`](buildozer/__init__.py) is the
single source of truth. `setup.py` reads it via a regex
(`find_version()`); GitHub Actions reads it from the pushed
tag. There is no `MANIFEST.in`, no PEP 621 metadata in `pyproject.toml`,
and no version-bump tooling, edit the string directly.

The post-release convention is to bump to a `.devN` suffix on `master`
(e.g. after releasing `1.5.0`, master moved to `1.5.1.dev0` in commit
`0689513`).

## Pre-release checklist

On `master`, before tagging:

1. **Verify CI is green.** Latest run of every workflow on `master`:

   ```bash
   gh run list --branch master --limit 8
   ```

   `Tests` (the Python 3.8–3.14 matrix), `iOS`, `Android Integration`,
   `Docker`, and `PyPI release` (build + `twine check`, no upload on
   non-tag pushes) should all show `success`.

2. **Update `__version__`** in `buildozer/__init__.py` to the target
   version (e.g. `1.5.1`), drop the `.devN` suffix.

3. **Regenerate `CHANGELOG.md`** with
   [github-changelog-generator](https://github.com/github-changelog-generator/github-changelog-generator):

   ```bash
   github_changelog_generator --user kivy --project buildozer --future-release 1.5.1
   ```

   Review the diff, prune noise as needed, and commit.

4. **Refresh Trove classifiers** in `setup.py` (`classifiers=[...]`) so
   the `Programming Language :: Python :: 3.x` entries match the CI
   matrix in `.github/workflows/test_python.yml`.

5. Land steps 2–4 as a PR titled e.g. `Release 1.5.1`.

## Cutting the release

After the release PR is merged:

```bash
git fetch origin
git checkout master
git pull --ff-only
git tag 1.5.1
git push origin 1.5.1
```

The tag push triggers `.github/workflows/pypi-release.yml`, which:

- runs `python -m build` (sdist + wheel),
- runs `twine check dist/*`,
- uploads to PyPI via `pypa/gh-action-pypi-publish` using the
  `pypi_password` repository secret. The publish step is gated on
  `startsWith(github.event.ref, 'refs/tags')`.

The same push also re-runs `.github/workflows/docker.yml`, which
publishes `kivy/buildozer:latest` to DockerHub and
`ghcr.io/kivy/buildozer:latest` to GHCR (the publish gate is
`refs/heads/master OR refs/tags/*`).

Tag naming convention: bare `1.5.1` (no `v` prefix), matching every
release tag from `1.0` onward.

## Post-release

1. **Verify the PyPI page**:
   <https://pypi.org/project/buildozer/> should show the new version.
   Confirm with `pip install buildozer==1.5.1` in a clean venv.

2. **Create a GitHub Release** via the web UI:
   <https://github.com/kivy/buildozer/releases/new>. Select the pushed
   tag, click **Generate release notes** to auto-fill the title and body
   from merged PRs, then **Publish release**.

3. **Announce the release** in the Kivy Discord `#announcements`
   channel:
   <https://discord.com/channels/423249981340778496/490505571271704577>.

4. **Bump master back to dev**: open a follow-up PR setting
   `__version__ = '1.5.2.dev0'` (or `1.6.0.dev0` if the next release
   will be a minor bump).

## Secrets used by the release pipeline

| Secret | Used by | Purpose |
|---|---|---|
| `pypi_password` | `pypi-release.yml` | PyPI API token for the upload step |
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | `docker.yml` | DockerHub login + image push, README sync |
| `GITHUB_TOKEN` | `docker.yml` | GHCR push (provided implicitly by Actions) |

## Not currently automated

- **Versioned Docker tags**: `docker.yml` only publishes `:latest`. No
  `kivy/buildozer:1.5.1` image is produced.
- **CHANGELOG generation**: semi-automated via
  `github-changelog-generator` (run locally, commit the result).
- **GitHub Release object**: manual (step 2 above).
- **Discord announcement**: manual (step 3 above).
- **Post-release dev bump**: manual (step 4 above).
