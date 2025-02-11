# CI/CD Pipeline Documentation

This document outlines the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Edify project. The pipeline is implemented using GitHub Actions and is designed to ensure code quality, run tests, and automate deployments.

## Branch Strategy

The repository maintains two main branches for the continuous development and integration pipeline:

- `main`: Primary development branch

  - All feature branches are merged here first
  - Code must pass all tests and lint checks before merging
  - Used for integration testing and staging

- `PROD`: Production branch
  - Only accepts merges from `main`
  - Any changes merged to this branch are automatically deployed
  - Represents the live production environment

## GitHub Actions Workflows

### 1. Linting Workflow

**File**: `.github/workflows/lint.yml`

This workflow automatically checks code quality on every push to any branch. It performs linting checks using pylint, examining both individual Python files and project-wide issues like cyclic imports and duplicate code.

### 2. Testing Workflow

**File**: `.github/workflows/tests.yml`

This workflow runs the test suite whenever code is pushed to main branches (main, master, DEV, PROD) or when pull requests are opened targeting those branches. It executes the full pytest test suite to verify functionality.

## Development Workflow

1. **Feature Development**

   - Create a new branch from `main`
   - Implement feature/fix (making regular and descriptive commits)
   - Run local tests and linting:

     ```bash
     # Run linting
     ./run_lint

     # Run tests
     poetry run pytest
     ```

2. **Code Review Process**

   - Create Pull Request to `main`
   - Automated checks run:
     - Linting workflow
     - Testing workflow
   - Peer review required
   - All checks must pass before merging

3. **Integration to Main**

   - Merge PR to `main` after approvals
   - Automated tests run again
   - Integration testing in staging environment

4. **Production Deployment**
   - Create PR from `main` to `PROD`
   - All tests and checks run again
   - After approval, merge to `PROD`
   - Automatic deployment triggers

## Deployment Configuration

The application is configured to run on different environments:

1. **Production:**

   - Uses production database URL
   - Requires HOST and PORT environment variables
   - HTTPS enforced
   - JWT cookies secured

2. **Local Development:**

   - Uses local database URL
   - Development server settings

3. **Testing:**
   - Uses in-memory SQLite database
   - Test-specific configurations

## Deployment Process

1. **Pre-deployment Checks**

   - All tests passing
   - Linting checks passed
   - Database migrations prepared
   - Environment variables configured

2. **Database Migration**

   When modifying database models, follow the steps outlined in the [database models documentation](MODELS.md#database-migrations)

3. **Application Deployment**

   Gunicorn server starts:

   ```bash
   gunicorn -b ${HOST}:${PORT} app:app
   ```

## Rollback Procedures

1. **Code Rollback**

   - Revert PROD branch to last known good commit
   - Automated deployment will handle the rest

2. **Database Rollback**

   - `flask db downgrade`

## Commit Guidelines

1. **Regular Commits**

   - Make small, focused commits
   - Commit frequently to track changes
   - Use meaningful commit messages
   - Follow conventional commits format:
     ```
     feat: add new feature
     fix: resolve bug
     docs: update documentation
     style: formatting changes
     refactor: code restructuring
     test: add/modify tests
     chore: maintenance tasks
     ```

2. **Pre-commit Checks**

   - Run linting before every commit: `./run_lint`
   - Fix any linting issues before committing
   - Run tests if changes affect functionality: `poetry run pytest`

3. **Branch Management**

   - Keep feature branches up to date with main
   - Rebase feature branches before merging
   - Delete branches after merging
   - Use meaningful branch names (similar to commits):

     ```
     feature/add-user-auth
     fix/login-error
     docs/update-readme
     chore/add-linting
     ```
