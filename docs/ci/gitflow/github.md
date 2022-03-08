
## Development Workflow
Add Github username and token as Github secrets.
```commandline
secrets.GIT_USERNAME
secrets.GIT_TOKEN
```

```yaml
name: Development Workflow
on:
  push:
    branches:
      - develop

jobs:
  upgrade-version:
    name: Upgrade Version
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v2
        with:
          fetch-depth: 0
      - name: Setup Git Author
        uses: fregante/setup-git-user@v1
      - name: Setup Python Env
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install Comet
        run: pip install --user .
      - name: Upgrade Version
        run: >-
              comet
              --debug
              --run branch-flow
              --scm-provider github
              --username ${{ secrets.GIT_USERNAME }}
              --password ${{ secrets.GIT_TOKEN }}
              --connection-type https
              --push
      - name: Upload Comet Config
        uses: actions/upload-artifact@v2
        with:
          name: comet-version
          path: .comet.yml
          retention-days: 1
```

## Stable Release Workflow
```yaml
name: Release
on: workflow_dispatch

jobs:
  release:
    name: Release to Stable Branch
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v2
        with:
          fetch-depth: 0
      - name: Setup Git Author
        uses: fregante/setup-git-user@v1
      - name: Setup Python Env
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install Comet
        run: pip install --user .
      - name: Upgrade Version
        run: >-
              comet
              --debug
              --run release
              --scm-provider github
              --username ${{ secrets.GIT_USERNAME }}
              --password ${{ secrets.GIT_TOKEN }}
              --connection-type https
              --push
      - name: Upload Comet Config
        uses: actions/upload-artifact@v2
        with:
          name: comet-version
          path: .comet.yml
          retention-days: 1
  sync:
    name: Sync Dev with Stable
    runs-on: ubuntu-latest
    needs:
      - release
    steps:
      - name: Sync Dev with Stable
        uses: benc-uk/workflow-dispatch@v1
        with:
          workflow: Sync
          token: ${{ secrets.GIT_TOKEN }}
          ref: master
```

## Synchronization Workflow
```yaml
name: Sync
on: workflow_dispatch

jobs:
  sync-with-dev:
    name: Sync Dev with Stable
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v2
        with:
          fetch-depth: 0
      - name: Setup Git Author
        uses: fregante/setup-git-user@v1
      - name: Setup Python Env
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install Comet
        run: pip install --user .
      - name: Upgrade Version
        run: >-
              comet
              --debug
              --run sync
              --scm-provider github
              --username ${{ secrets.GIT_USERNAME }}
              --password ${{ secrets.GIT_TOKEN }}
              --connection-type https
              --push
```