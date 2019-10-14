import re
import pathlib
import collections

import git
import git.exc
from clldutils.misc import lazyproperty

__all__ = ['Repository']


class Repository:
    """
    A (clone of a) git repository.
    """
    def __init__(self, path):
        try:
            self.repo = git.Repo(str(path))
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
            raise ValueError('invalid git repository: {0}'.format(path))

    @property
    def dir(self):
        """
        :return: The path of the repository clone as `pathlib.Path`.
        """
        return pathlib.Path(self.repo.working_dir)

    @lazyproperty
    def url(self):
        """
        :return: The URL of the remote called `origin` - if it is set, else `None`.
        """
        try:
            url = self.repo.remotes.origin.url
            if url.endswith('.git'):
                url = url[:-4]
            return url
        except AttributeError:  # pragma: no cover
            return

    @lazyproperty
    def github_repo(self):
        match = re.search('github\.com/(?P<org>[^/]+)/(?P<repo>[^.]+)', self.url or '')
        if match:
            return match.group('org') + '/' + match.group('repo')

    @property
    def tags(self):
        """
        :return: `list` of tags available for the repository. A tag can be used as `spec` argument \
        for `Repository.checkout`
        """
        return self.repo.git.tag().split()

    def describe(self):
        return self.repo.git.describe('--always', '--tags')

    def checkout(self, spec):
        return self.repo.git.checkout(spec)

    def json_ld(self, **dc):
        """
        A repository description in JSON-LD - suitable for inclusion in CLDF metadata.
        """
        res = collections.OrderedDict([
            ('rdf:type', 'prov:Entity'),
            ('dc:title', self.__class__.__name__),
        ])
        if self.url:
            res['rdf:about'] = self.url
        res['dc:created'] = self.describe()
        res.update({'dc:{0}'.format(k): dc[k] for k in sorted(dc)})
        return res
