"""
Exceptions for package configuration
"""

from fastoad.exceptions import FastError


class FASTConfigurationBaseKeyBuildingError(FastError):
    """
    Class for being raised from bottom to top of TOML dict so that in the end, the message
    provides the full qualified name of the problematic key.

    using `new_err = FASTConfigurationBaseKeyBuildingError(err, 'new_err_key', <value>)`:

    - if err is a FASTConfigurationBaseKeyBuildingError instance with err.key=='err_key':
        - new_err.key will be 'new_err_key.err_key'
        - new_err.value will be err.value (no need to provide a value here)
        - new_err.original_exception will be err.original_exception
    - otherwise, new_err.key will be 'new_err_key' and new_err.value will be <value>
        - new_err.key will be 'new_err_key'
        - new_err.value will be <value>
        - new_err.original_exception will be err

    :param original_exception: the error that happened for raising this one
    :param key: the current key
    :param value: the current value
    """

    def __init__(self, original_exception: Exception, key: str, value=None):
        """Constructor"""

        self.key = None
        """
        the "qualified key" (like "problem.group.component1") related to error, build
        through raising up the error
        """

        self.value = None
        """ the value related to error """

        self.original_exception = None
        """ the original error, when eval failed """

        if hasattr(original_exception, "key"):
            self.key = "%s.%s" % (key, original_exception.key)
        else:
            self.key = key
        if hasattr(original_exception, "value"):
            self.value = "%s.%s" % (value, original_exception.value)
        else:
            self.value = value
        if hasattr(original_exception, "original_exception"):
            self.original_exception = original_exception.original_exception
        else:
            self.original_exception = original_exception
        super().__init__(
            self,
            'Attribute or value not recognized : %s = "%s"\nOriginal error: %s'
            % (self.key, self.value, self.original_exception),
        )


class FASTConfigurationBadOpenMDAOInstructionError(FASTConfigurationBaseKeyBuildingError):
    """Class for managing errors that result from trying to set an attribute by eval."""
