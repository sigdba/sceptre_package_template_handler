# A Package Manager For Sceptre
## Quick Start

Install the module using `pip`:

``` sh
pip install -U sceptre-package-template-handler
```

**or** if you're using [docker-dev](https://github.com/sigdba/docker-dev), add
`sceptre-package-template-handler` to `requirements.txt` and restart docker-dev.

Create a repository variable in `sceptre/config/config.yaml`:

``` yaml
sig_repo:
  name: sig-shared-sceptre
  base_url: https://github.com/sigdba/sig-shared-sceptre
```

In your stack configuration, use the `package` template handler:

``` yaml
template:
  type: package
  name: EcsWebService
  release: 5
  repository: {{ sig_repo }}
```

**Note:** The `template` block replaces `template_path` in a Sceptre stack
          configuration.
          
## Introduction

The package template handler works by downloading versioned zip files from a
"repository" web site. The packages are unzipped into the Sceptre repository so
that they can be retained in local version control. All packages are versioned
to ensure that all changes are opt-in.

## Repository Configuration

The `repository` object supports the following keys:

- `name` - string - **required** - The name of the repository. This should be
  unique and is used to name the sub-directory of `templates` into which packages
  will be installed.
- `base_url` - string - **required** - The URL of the repository. In a
  GitHub-hosted repository, this will usually be the root page.
- `template_zip_url_format` - string - A string which will be passed to
  [Python's string formatter](https://docs.python.org/3.9/tutorial/inputoutput.html#the-string-format-method)
  to compute the URL for a given package.
  - **Default:** `"{repo.base_url}/releases/download/r{release}/{package_name}-{release}.zip`
  - The formatter will pass the following values:
    - `repo` - The `repository` object itself.
    - `package_name` - The `name` value from `template`.
    - `release` - The `release` value from `template`.
    
## Hosting a Repository

All that is required to host a repository is a website in which the packages are
available at consistent URLs. For an example, see
[sig-shared-sceptre](https://github.com/sigdba/sig-shared-sceptre) where
packages are published under releases. It also includes [a GitHub
workflow](https://github.com/sigdba/sig-shared-sceptre/blob/main/.github/workflows/package.yml)
to automatically document and publish new releases.
