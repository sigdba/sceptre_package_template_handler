import jsonschema
import yaml
import zipfile
import urllib.request
import urllib.error
import tempfile
import shutil

from os import path

import sceptre.template_handlers.file

from sceptre.template_handlers import TemplateHandler
from sceptre.helpers import normalise_path
from sceptre.exceptions import SceptreException

REPO_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "base_url": {"type": "string"},
        "template_zip_url_format": {"type": "string"},
    },
    "required": ["name", "base_url"],
}

MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {"entrypoint": {"type": "string"}},
    "required": ["entrypoint"],
}


def path_is_parent(parent_path, child_path):
    parent_path = path.abspath(parent_path)
    child_path = path.abspath(child_path)
    return path.commonpath([parent_path]) == path.commonpath([parent_path, child_path])


class PackageTemplateError(SceptreException):
    pass


class ValidatedObject(object):
    def __init__(self, schema, spec, defaults={}):
        jsonschema.validate(spec, schema)
        self._spec = spec
        self._defaults = defaults

    def __getattr__(self, attr):
        if attr in self._spec:
            return self._spec[attr]
        return self._default(attr)

    def _default(self, attr):
        return self._defaults.get(attr)


class PackageRepository(ValidatedObject):
    def __init__(self, spec):
        super(PackageRepository, self).__init__(
            REPO_SCHEMA,
            spec,
            defaults={
                "template_zip_url_format": "{repo.base_url}/releases/download/r{release}/{package_name}-{release}.zip"
            },
        )

    def template_zip_url(self, package_name, release):
        return self.template_zip_url_format.format(
            package_name=package_name, release=release, repo=self
        )


class Manifest(ValidatedObject):
    def __init__(self, spec):
        super(Manifest, self).__init__(MANIFEST_SCHEMA, spec)


class PackageTemplateHandler(TemplateHandler):
    """
    The following instance attributes are inherited from the parent class TemplateHandler.

    Parameters
    ----------
    name: str
        The name of the template. Corresponds to the name of the Stack this template belongs to.
    handler_config: dict
        Configuration of the template handler. All properties except for `type` are available.
    sceptre_user_data: dict
        Sceptre user data defined in the Stack config
    connection_manager: sceptre.connection_manager.ConnectionManager
        Connection manager that can be used to call AWS APIs
    """

    def __init__(self, *args, **kwargs):
        super(PackageTemplateHandler, self).__init__(*args, **kwargs)
        # print(yaml.dump({"args": args, "kwargs": kwargs}))
        self._args = args
        self._kwargs = kwargs

    def schema(self):
        """
        Return a JSON schema of the properties that this template handler requires.
        For help filling this, see https://github.com/Julian/jsonschema
        """
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "release": {"type": ["number", "string"]},
                "repository": REPO_SCHEMA,
            },
            "required": ["name", "release", "repository"],
        }

    def handle(self):
        """
        `handle` should return a CloudFormation template string or bytes. If the return
        value is a byte array, UTF-8 encoding is assumed.

        To use instance attribute self.<attribute_name>. See the class-level docs for a
        list of attributes that are inherited.

        Returns
        -------
        str|bytes
            CloudFormation template
        """
        repo = PackageRepository(self.arguments["repository"])
        pkg_name = self.arguments["name"]
        pkg_release = str(self.arguments["release"])
        templates_path = path.join(self.stack_group_config["project_path"], "templates")
        pkg_dir = path.join(
            templates_path, normalise_path(f"{repo.name}/{pkg_name}-{pkg_release}")
        )

        if not path.exists(pkg_dir):
            self.download(repo, pkg_name, pkg_release, pkg_dir)

        manifest_path = path.join(pkg_dir, "manifest.yaml")
        if not path.exists(manifest_path):
            raise PackageTemplateError(f"package manifest not found: {manifest_path}")
        with open(manifest_path, "r") as fp:
            manifest = Manifest(yaml.safe_load(fp))
        template_path = path.join(pkg_dir, manifest.entrypoint)
        if not path_is_parent(pkg_dir, template_path):
            raise PackageTemplateError(f"Invalid entrypoint: {manifest.entrypoint}")

        return sceptre.template_handlers.file.File(
            *self._args,
            **{
                **self._kwargs,
                "arguments": {
                    "path": path.relpath(template_path, start=templates_path)
                },
            },
        ).handle()

    def download(self, repo, pkg_name, pkg_release, pkg_dir):
        zip_url = repo.template_zip_url(pkg_name, pkg_release)
        req = urllib.request.Request(zip_url)
        self.logger.info("Downloading %s", zip_url)
        try:
            with urllib.request.urlopen(req) as resp:
                with tempfile.NamedTemporaryFile("w+b") as fp:
                    shutil.copyfileobj(resp, fp)
                    fp.seek(0)
                    zipfile.ZipFile(fp).extractall(pkg_dir)
        except (urllib.error.HTTPError) as e:
            self.logger.fatal("Error downloading template %s: %s", zip_url, e)
