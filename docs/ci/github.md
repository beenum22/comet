```yaml
name: Development Branch
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