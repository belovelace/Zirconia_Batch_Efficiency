module.exports = {
  root: true,
  env: { node: true, es2022: true, browser: true, jest: true },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json'],
    tsconfigRootDir: __dirname,
  },
  plugins: [
    '@typescript-eslint',
    'import',
    'unicorn',
    'security',
    'sonarjs',
    'jsdoc',
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'airbnb-typescript/base',
    'plugin:unicorn/recommended',
    'plugin:sonarjs/recommended',
    'plugin:security/recommended',
    'plugin:jsdoc/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier',
  ],
  settings: {
    'import/resolver': { typescript: {} },
  },
  rules: {
    'no-console': ['error', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'consistent-return': 'error',
    'import/no-default-export': 'error',
    'import/no-extraneous-dependencies': ['error', { devDependencies: false }],
    'unicorn/prefer-module': 'off',
    'unicorn/filename-case': ['error', { case: 'kebabCase' }],

    '@typescript-eslint/explicit-function-return-type': ['error', { allowExpressions: false }],
    '@typescript-eslint/explicit-module-boundary-types': 'error',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/strict-boolean-expressions': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/prefer-readonly': 'error',
    '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],

    'sonarjs/cognitive-complexity': ['error', 15],
    'security/detect-unsafe-regex': 'error',

    'jsdoc/require-jsdoc': ['warn', {
      contexts: ['FunctionDeclaration', 'MethodDefinition', 'ClassDeclaration'],
    }],

    'arrow-body-style': ['error', 'as-needed'],

    'max-lines-per-function': ['warn', { max: 200 }],
    'max-params': ['warn', 4],
  },
  overrides: [
    {
      files: ['**/*.test.ts', '**/*.spec.ts', 'tests/**'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        'jsdoc/require-jsdoc': 'off',
      },
    },
  ],
};
