```yaml
#----------------------------------------------------------------------------------------------------------------------#
# Important Notes:
#----------------------------------------------------------------------------------------------------------------------#
#   - Release pipelines should only be executed by the repository administrators
#   - All commits should follow conventional commits specification (https://www.conventionalcommits.org/) if
#     'auto' release option is used
#   - Feature/bugfix branches should be merged to development branch (develop) using squash merge strategy
#   - Hotfix branches should be merged to stable branch (master) using squash merge strategy
#   - Release branches should NOT be merged to stable branch (master) using squash merge strategy
#   - Stable branch should NOT be merged to development branch (develop) using squash merge strategy
#   - Branch permissions should be disabled for stable (master) and development (develop) branches
#----------------------------------------------------------------------------------------------------------------------#
# Required Bitbucket Pipelines Global environment variables
#----------------------------------------------------------------------------------------------------------------------#
# - BITBUCKET_USERNAME
#     Description:
#       Sets Bitbucket username.
#       e.g. muneeb-ahmad
# - BITBUCKET_APP_PASSWORD
#     Description:
#       Sets Bitbucket App password with admin repo privileges.
# - DOCKER_HUB_USERNAME
#     Description:
#       Sets ng-voice Docker registry username.
# - DOCKER_HUB_PASSWORD
#     Description:
#       Sets ng-voice Docker registry password.
# -----
image: atlassian/default-image:2

options:
  docker: true

definitions:
  steps:

    - step: &shared-vars
        name: Generate shared variables file
        clone:
          enabled: false
        script:
          -
        artifacts:
          - shared_vars.sh

    - step: &lint-last-message
        name: Lint Commit Message
        image: gtramontina/commitlint:8.3.5
        script:
          - commitlint --config .commitlint.js --from HEAD~1

    - step: &push-comet-upgrades
        name: Push Comet Upgrades
        clone:
          depth: full
        script:
          - git log
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - git push origin

    - step: &release-candidate
        name: Generate Release Candidate
        image:
          name: dockerhub.ng-voice.com/comet:0.2.0-dev.11
          username: $DOCKER_HUB_USERNAME
          password: $DOCKER_HUB_PASSWORD
        clone:
          depth: full
        script:
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - >-
            comet
            --debug
            --run release-candidate
            --username ${BITBUCKET_USERNAME}
            --password ${BITBUCKET_APP_PASSWORD}
            --connection-type https
            --push

    - step: &release
        name: Release version
        image:
          name: dockerhub.ng-voice.com/comet:0.2.0-dev.11
          username: $DOCKER_HUB_USERNAME
          password: $DOCKER_HUB_PASSWORD
        clone:
          depth: full
        script:
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - >-
            comet
            --debug
            --run release
            --username ${BITBUCKET_USERNAME}
            --password ${BITBUCKET_APP_PASSWORD}
            --connection-type https
            --push

    - step: &upgrade-version
        name: Upgrade Version
        image:
          name: dockerhub.ng-voice.com/comet:0.2.0-dev.11
          username: $DOCKER_HUB_USERNAME
          password: $DOCKER_HUB_PASSWORD
        clone:
          depth: full
        script:
          - >-
            if [ -f "shared_vars.sh" ]; then
              source shared_vars.sh
              rm shared_vars.sh
            fi
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - >-
            comet
            --debug
            --run branch-flow
            --username ${BITBUCKET_USERNAME}
            --password ${BITBUCKET_APP_PASSWORD}
            --connection-type https
            ${PUSH:+--push}

    - step: &execute-comet-unit-tests
        name: Run Unit tests
        image: python:3.7.2
        condition:
          changesets:
            includePaths:
              - "src/comet/**"
              - "tests/**"
              - Dockerfile
              - setup.py
              - pyproject.toml
        script:
          - pip install -e .
          - python -m unittest discover -s tests/

    - step: &build-and-push-comet
        name: Build & Push Comet
        condition:
          changesets:
            includePaths:
              - "src/comet/**"
              - "tests/**"
              - Dockerfile
              - setup.py
              - pyproject.toml
        caches:
          - docker
        script:
          - >-
            if [ -f "shared_vars.sh" ]; then
              source shared_vars.sh
            fi
          - export IMAGE_NAME=dockerhub.ng-voice.com/comet
          - 'export IMAGE_TAG=$(grep "dev_version:" .comet.yml | sed "s/^.*: //" | tr + _)'
          - echo "${IMAGE_NAME}:${IMAGE_TAG}"
          - docker login --username $DOCKER_HUB_USERNAME --password $DOCKER_HUB_PASSWORD dockerhub.ng-voice.com
          - >-
            docker build -t ${IMAGE_NAME}:${IMAGE_TAG}
            -f Dockerfile .
          - docker push ${IMAGE_NAME}:${IMAGE_TAG}
          - >-
            if [[ -v STABLE_BRANCH ]]; then
              docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
              docker push ${IMAGE_NAME}:latest
            fi

pipelines:
  custom:
    release:
      - step: *release

    release-candidate:
      - step: *release-candidate

  default:
    - step: *lint-last-message
    - step:
        <<: *upgrade-version
        name: Generate Comet Config
        artifacts:
          - "**"
          - ".**"
    - step: *execute-comet-unit-tests
    - step: *build-and-push-comet
    - step: *push-comet-upgrades

  branches:
    develop:
      - step: *lint-last-message
      - step:
          <<: *upgrade-version
          name: Generate Comet Config
          artifacts:
            - "**"
            - ".**"
      - step: *execute-comet-unit-tests
      - step: *build-and-push-comet
      - step: *push-comet-upgrades

    master:
      - step: *lint-last-message
      - step:
          <<: *upgrade-version
          name: Generate Comet Config
          artifacts:
            - "**"
            - ".**"
      - step: *execute-comet-unit-tests
      - step: *build-and-push-comet
      - step: *push-comet-upgrades

    release/**:
      - step: *lint-last-message
      - step:
          <<: *upgrade-version
          name: Generate Comet Config
          artifacts:
            - "**"
            - ".**"
      - step: *execute-comet-unit-tests
      - step: *build-and-push-comet
      - step: *push-comet-upgrades
```