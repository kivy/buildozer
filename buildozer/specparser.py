"""
    A customised ConfigParser, suitable for buildozer.spec.

    Supports
        - list values
            - either comma separated, or in their own [section:option] section.
        - environment variable overrides of values
            - overrides applied at construction.
        - case-sensitive keys
        - "No values" are permitted.
"""

from configparser import ConfigParser
from os import environ


class SpecParser(ConfigParser):
    def __init__(self, *args, **kwargs):
        # Allow "no value" options to better support lists.
        super().__init__(*args, allow_no_value=True, **kwargs)

    def optionxform(self, optionstr: str) -> str:
        """Override method that canonicalizes keys to retain
        case sensitivity."""
        return optionstr

    # Override all the readers to apply env variables over the top.

    def read(self, filenames, encoding=None):
        super().read(filenames, encoding)
        # Let environment variables override the values
        self._override_config_from_envs()

    def read_file(self, f, source=None):
        super().read_file(f, source)
        # Let environment variables override the values
        self._override_config_from_envs()

    def read_string(self, string, source="<string>"):
        super().read_string(string, source)
        # Let environment variables override the values
        self._override_config_from_envs()

    def read_dict(self, dictionary, source="<dict>"):
        super().read_dict(dictionary, source)
        # Let environment variables override the values
        self._override_config_from_envs()

    # Add new getters

    def getlist(
        self, section, token, default=None, with_values=False, strip=True,
        section_sep="=", split_char=","
    ):
        """Return a list of strings.

        They can be found as the list of options in a [section:token] section,
        or in a [section], under the a option, as a comma-separated (or
        split_char-separated) list,
        Failing that, default is returned (as is).

        If with_values is set, and they are in a [section:token] section,
        the option values are included with the option key,
        separated by section_sep
        """

        # if a section:token is defined, let's use the content as a list.
        l_section = "{}:{}".format(section, token)
        if self.has_section(l_section):
            values = self.options(l_section)
            if with_values:
                return [
                    "{}{}{}".format(key, section_sep, self.get(l_section, key))
                    for key in values
                ]
            return values if not strip else [x.strip() for x in values]
        values = self.getdefault(section, token, None)
        if values is None:
            return default
        values = values.split(split_char)
        if not values:
            return default
        return values if not strip else [x.strip() for x in values]

    def getlistvalues(self, section, token, default=None):
        """ Convenience function.
            Deprecated - call getlist directly."""
        return self.getlist(section, token, default, with_values=True)

    def getdefault(self, section, token, default=None):
        """
        Convenience function.
        Deprecated - call get directly."""
        return self.get(section, token, fallback=default)

    def getbooldefault(self, section, token, default=False):
        """
        Convenience function.
        Deprecated - call getboolean directly."""
        return self.getboolean(section, token, fallback=default)

    # Handle env vars.

    def _override_config_from_envs(self):
        """Takes a ConfigParser, and checks every section/token for an
        environment variable of the form SECTION_TOKEN, with any dots
        replaced by underscores. If the variable exists, sets the config
        variable to the env value.
        """
        for section in self.sections():
            for token in self.options(section):
                self._override_config_token_from_env(section, token)

    def _override_config_token_from_env(self, section, token):
        """Given a config section and token, checks for an appropriate
        environment variable. If the variable exists, sets the config entry to
        its value.

        The environment variable checked is of the form SECTION_TOKEN, all
        upper case, with any dots replaced by underscores.

        """
        env_var_name = "_".join(
            item.upper().replace(".", "_") for item in (section, token)
        )
        env_var = environ.get(env_var_name)
        if env_var is not None:
            self.set(section, token, env_var)
