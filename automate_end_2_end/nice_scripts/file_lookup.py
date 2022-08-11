import os
import gitlab
from dotenv import load_dotenv
import os
import json
from base64 import b64decode

import time
load_dotenv()
class FileLookup():
    """Retrieve files from a local filesystem or remote GitLab Server.

    When _runway_dir_ is specified, the local directory is given priority and
    remote Git Server will not be used.

    Args:
        git_short (str): Short Git representation of repository, e.g.
            forrest/core.
        runway_dir (str): Root of local runway directory to use instead of
            accessing Git.
    """

    def __init__(self, project='',git_short = '', runway_dir=''):
        self.project = project
        self.runway_dir = os.path.expandvars(os.path.expanduser(runway_dir))
        self.git_short = git_short
        self.server = None
        self.project = project

        if not self.runway_dir:
            self.get_gitlab_project()

    def get_gitlab_project(self):
        """Get numerical GitLab Project ID.

        Returns:
            int: Project ID number.

        Raises:
            foremast.exceptions.GitLabApiError: GitLab responded with bad status
                code.

        """
        # self.server = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
        # project = self.server.projects.get(self.project_id)

        if not self.project:
            raise Exception('Could not get Project "{0}" from GitLab API.'.format(self.git_short))

        # self.project = project
        return self.project

    def local_file(self, filename):
        """Read the local file in _self.runway_dir_.

        Args:
            filename (str): Name of file to retrieve relative to root of
                _runway_dir_.

        Returns:
            str: Contents of local file.

        Raises:
            FileNotFoundError: Requested file missing.

        """
        print('Retrieving "%s" from "%s".', filename, self.runway_dir)

        file_contents = ''

        file_path = os.path.join(self.runway_dir, filename)

        try:
            with open(file_path, 'rt') as lookup_file:
                file_contents = lookup_file.read()
        except FileNotFoundError:
            print('File missing "%s".', file_path)
            raise

        print('Local file contents:\n%s', file_contents)
        return file_contents

    def remote_file(self, branch='master', filename=''):
        """Read the remote file on Git Server.

        Args:
            branch (str): Git Branch to find file.
            filename (str): Name of file to retrieve relative to root of
                repository.

        Returns:
            str: Contents of remote file.

        Raises:
            FileNotFoundError: Requested file missing.

        """
        # print('Retrieving "%s" from "%s".', filename, self.git_short)

        file_contents = ''

        try:
            file_blob = self.project.files.get(file_path=filename, ref=branch)
        except gitlab.exceptions.GitlabGetError:
            file_blob = None

        # print('GitLab file response:\n%s', file_blob)

        if not file_blob:
            msg = 'Project "{0}" is missing file "{1}" in "{2}" branch.'.format(self.git_short, filename, branch)
            print(msg)
            raise FileNotFoundError(msg)

        file_contents = b64decode(file_blob.content).decode()

        # print('Remote file contents:\n%s', file_contents)
        return file_contents

    def get(self, branch='master', filename=''):
        """Retrieve _filename_ from GitLab.

        Args:
            branch (str): Git Branch to find file.
            filename (str): Name of file to retrieve relative to root of Git
                repository, or _runway_dir_ if specified.

        Returns:
            str: Contents of file.

        """
        file_contents = ''

        if self.runway_dir:
            file_contents = self.local_file(filename=filename)
        else:
            file_contents = self.remote_file(branch=branch, filename=filename)

        return file_contents

    def json(self, branch='master', filename=''):
        """Retrieve _filename_ from GitLab.

        Args:
            branch (str): Git Branch to find file.
            filename (str): Name of file to retrieve.

        Returns:
            dict: Decoded JSON.

        Raises:
            SystemExit: Invalid JSON provided.

        """
        file_contents = self.get(branch=branch, filename=filename)

        try:
            json_dict = json.loads(file_contents)
        # TODO: Use json.JSONDecodeError when Python 3.4 has been deprecated
        except ValueError as error:
            msg = ('"{filename}" appears to be invalid json. '
                   'Please validate it with http://jsonlint.com. '
                   'JSON decoder error:\n'
                   '{error}').format(
                       filename=filename, error=error)
            raise SystemExit(msg)

        print('JSON object:\n%s', json_dict)
        return json_dict