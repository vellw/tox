import os, sys
import py
configparser = py.builtin._tryimport("ConfigParser", "configparser")

class Config:
    def __init__(self):
        self.envconfigs = {}

class ConfigError(Exception):
    """ error in tox configuration. """

class VenvConfig:
    def __init__(self, **kw):
        self.__dict__.update(kw)

testenvprefix = "testenv:"

def parseini(path):
    cfg = configparser.RawConfigParser()
    cfg.read(str(path))
    projdir = py.path.local(path).dirpath()
    parser = ConfigIniParser(cfg, projdir)
    return parser.config

class ConfigIniParser:
    def __init__(self, cfg, projdir):
        self._cfg = cfg
        self.config = config = Config()
        config.projdir = projdir
        config._parser = self
        config.toxdir = py.path.local(
            self.getdefault("global", "toxdir", ".tox"))
        sections = cfg.sections()
        for section in sections:
            if section.startswith(testenvprefix):
                name = section[len(testenvprefix):]
                config.envconfigs[name] = self._makeenvconfig(name, section)
        if not config.envconfigs:
            config.envconfigs['python'] = self._makeenvconfig("python", "_xz_9")

    def _makeenvconfig(self, name, section):
        vc = VenvConfig(name=name)
        vc.envdir = self.config.toxdir.join(name)
        vc.python = self.getdefault(section, "python", None)
        vc.command = self.getdefault(section, "command", None)
        vc.deps = self.getlist(section, "deps")
        vc.changedir = py.path.local(
            self.getdefault(section, "changedir", self.config.projdir))
        downloadcache = self.getdefault(section, "downloadcache")
        if downloadcache is None:
            downloadcache = os.environ.get("PIP_DOWNLOAD_CACHE", "")
            if not downloadcache:
                downloadcache = self.config.toxdir.join("_download")
        vc.downloadcache = py.path.local(downloadcache)
        return vc

    def getlist(self, section, name, sep="\n"):
        s = self.getdefault(section, name, None)
        if s is None:
            return []
        return [x.strip() for x in s.split(sep) if x.strip()]

    def getdefault(self, section, name, default=None):
        try:
            return self._cfg.get(section, name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            try:
                return self._cfg.get("test", name)
            except (configparser.NoSectionError, configparser.NoOptionError):
                return default
