class LayraError(Exception):
    """
    Base exception for all Layra errors.
    """
    pass


class TemplateLoadError(LayraError):
    """
    Templates load errors.
    """
    pass


class ValidationError(LayraError):
    """
    Validation errors.
    """
    pass


class ProjectError(LayraError):
    """
    Project creation errors.
    """
    pass


class ParseError(LayraError):
    """
    Any parsing errors.
    """
    pass


class GitError(LayraError):
    pass


class CloneError(GitError):
    pass
