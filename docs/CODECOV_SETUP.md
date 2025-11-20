# Codecov Setup Guide

This guide walks you through setting up Codecov integration for code coverage reporting.

## 📋 Prerequisites

- GitHub repository: `ideiasfactory/brazillian_cds_datafeeder_v2`
- Admin access to the repository
- Tests with coverage reporting already configured (✅ done)

## 🚀 Setup Steps

### 1. Sign Up for Codecov

1. Go to [codecov.io](https://codecov.io/)
2. Click "Sign up" and choose "Sign in with GitHub"
3. Authorize Codecov to access your GitHub account

### 2. Add Repository to Codecov

1. After signing in, you'll see your GitHub repositories
2. Find `brazillian_cds_datafeeder_v2` in the list
3. Click "Setup repo" or enable it

### 3. Get Your Codecov Token

Once the repo is added:

1. Go to repository settings in Codecov
2. Find the "Upload token" section
3. Copy the token (it looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### 4. Add Token to GitHub Secrets

1. Go to your GitHub repository: https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `CODECOV_TOKEN`
5. Value: Paste the token from Codecov
6. Click **Add secret**

### 5. Verify Integration

After adding the secret:

1. Push a commit or manually trigger the workflow:
   ```bash
   git commit --allow-empty -m "ci: test codecov integration"
   git push origin master
   ```

2. Go to **Actions** tab in GitHub to watch the workflow run

3. Once complete, check Codecov dashboard for coverage report

4. The badge should now show the coverage percentage instead of "unknown"

## 🎯 Expected Results

After successful setup:

- ✅ **Tests Badge**: Shows "passing" with green checkmark
- ✅ **Codecov Badge**: Shows coverage percentage (e.g., "55%")
- ✅ **Coverage Reports**: Available in Codecov dashboard
- ✅ **PR Comments**: Codecov will comment on PRs with coverage changes

## 📊 Current Configuration

Our workflow (`.github/workflows/tests.yml`) already includes:

```yaml
- name: Upload coverage reports to Codecov
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: false
  env:
    CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

## 🔧 Troubleshooting

### Badge shows "unknown"
- Verify `CODECOV_TOKEN` is added to GitHub Secrets
- Check that the workflow ran successfully
- Ensure `coverage.xml` is being generated

### Workflow fails on Codecov upload
- Check GitHub Actions logs for error messages
- Verify the token is correct
- Try setting `fail_ci_if_error: false` (already set)

### Coverage not updating
- Clear Codecov cache
- Re-run the workflow
- Check that tests are actually running

## 📚 Additional Resources

- [Codecov Documentation](https://docs.codecov.com/)
- [GitHub Actions Integration](https://docs.codecov.com/docs/github-actions)
- [Codecov Badge](https://docs.codecov.com/docs/status-badges)

## ✅ Quick Checklist

- [ ] Sign up for Codecov
- [ ] Add repository to Codecov
- [ ] Copy Codecov upload token
- [ ] Add `CODECOV_TOKEN` to GitHub Secrets
- [ ] Trigger workflow (push commit)
- [ ] Verify badges are showing correctly
- [ ] Check coverage report in Codecov dashboard

---

**Note**: The badge in README.md is already configured correctly:
```markdown
[![codecov](https://codecov.io/gh/ideiasfactory/brazillian_cds_datafeeder_v2/branch/master/graph/badge.svg)](https://codecov.io/gh/ideiasfactory/brazillian_cds_datafeeder_v2)
```
