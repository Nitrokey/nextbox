import re
import os
from pathlib import Path


class TemplatesDirectoryNotFound(IOError): pass
class PlaceholderDataMissingError(KeyError): pass
class FileNotFoundError(KeyError): pass
class FileNotFoundInMappingError(FileNotFoundError): pass

class SystemFiles:

    placeholder_pat = re.compile("%%([^%]+)%%")

    system_files_map = {
        "dphys-swapfile": "/etc/dphys-swapfile",
        "nitrokey-nextbox.list": "/etc/apt/sources.list.d/nitrokey-nextbox.list",
        "50unattended-upgrades": "/etc/apt/apt.conf.d/50unattended-upgrades",
        "journald.conf": "/etc/systemd/journald.conf",
        "ddclient": "/etc/default/ddclient",
        "nextbox-updater": "/etc/default/nextbox-updater",
        "php.load": "/srv/apache2/mods-available/php.load",
        "cmdline.txt": "/boot/cmdline.txt"
    }

    def __init__(self, template_dir, log_obj):
        p = Path(template_dir) 
        if not p.exists():
            raise TemplatesDirectoryNotFound(template_dir)

        self.template_files = os.listdir(template_dir)
        self.template_dir = template_dir
        self.log = log_obj


    def safe_ensure_file(self, which, **data):
        self.log.info(f"checking file: '{self.system_files_map.get(which)}'")
        try:
            ret = self.ensure_file(which, **data)
        except Exception as e:
            self.log.info(f"Exception thrown, skipping: '{self.system_files_map.get(which)}'", exc_info=e)
            return False

        if ret:
            self.log.info(f"updated file: '{self.system_files_map.get(which)}'")
        return ret

    def safe_ensure_not_empty_file(self, which, **data):
        self.log.info(f"checking file (for existance only): '{self.system_files_map.get(which)}'")
        try:
            ret = self.ensure_not_empty_file(which, **data)
        except Exception as e:
            self.log.info(f"Exception thrown, skipping: '{self.system_files_map.get(which)}'", exc_info=e)
            return False
                    
        if ret:
            self.log.info(f"created default file: '{self.system_files_map.get(which)}'")
        return ret

    def ensure_file(self, which, **data):
        if which not in self.template_files:
            raise FileNotFoundError(which)
        if which not in self.system_files_map:
            raise FileNotFoundInMappingError(which)

        # find/read current and replace if required
        content = self.get_content(self.system_files_map[which])
        final_content = self.get_final_content(which, **data)

        if content != final_content:
            with Path(self.system_files_map[which]).open("w") as fd:
                fd.write(final_content)
            return True
        return False

    def ensure_not_empty_file(self, which, **data):
        if which not in self.template_files:
            raise FileNotFoundError(which)
        if which not in self.system_files_map:
            raise FileNotFoundInMappingError(which)

        # find/read current and replace if required
        content = self.get_content(self.system_files_map[which])
        final_content = self.get_final_content(which, **data)

        if content.strip() == '':
            with Path(self.system_files_map[which]).open("w") as fd:
                fd.write(final_content)
            return True
        return False

    def ensure_deleted_file(self, path):
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False

    def ensure_symlink(self, target, source):
        p = Path(source)
        if not p.exists():
            p.symlink_to(target)
            return True
        return False

    def get_content(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        if not path.exists():
            return ""

        with path.open("r") as fd:
            return fd.read()

    def get_final_content(self, which, **data):
        tmpl = self.get_content(Path(self.template_dir) / which)
        return self.replace_placeholders(tmpl, **data)

    def get_placeholders(self, s):
        return self.placeholder_pat.findall(s)

    def replace_placeholders(self, s, **data):
        avail_keys = self.get_placeholders(s)
        missing = [key for key in avail_keys if key not in data]
        if len(missing) > 0:
            raise PlaceholderDataMissingError(", ".join(missing))

        for key in avail_keys:
            s = s.replace(f"%%{key}%%", data[key])
        return s
            


