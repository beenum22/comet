module.exports = {
    "rules": {
                'header-max-length': [2, 'always', 100],
                'type-case': [2, 'always', 'lower-case'],
                'type-empty': [2, 'never'],
                'type-enum': [
                        2,
                        'always',
                        [
                                'build',
                                'chore',
                                'ci',
                                'docs',
                                'feat',
                                'fix',
                                'perf',
                                'refactor',
                                'revert',
                                'style',
                                'test',
                        ],
                ],
                'scope-case': [2, 'always', 'lower-case'],
                'subject-case': [
                        2,
                        'never',
                        [
                            'sentence-case',
                            'start-case',
                            'pascal-case',
                            'upper-case',
                            'camel-case'
                        ],
                ],
                'subject-empty': [2, 'never'],
                'subject-full-stop': [2, 'never', '.'],
        'body-leading-blank': [2, 'always'],
                'body-max-line-length': [1, 'always', 100],
                'footer-leading-blank': [1, 'always'],
                'footer-max-line-length': [2, 'always', 100]
    },
    extends: ['@commitlint/config-conventional']
    }