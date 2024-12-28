# advc.009: A minimalistic way to access the BUG config files prior to the
# initialization of the BUG engine. Because some options just need to
# take effect already on the opening menu or even earlier. Not itself a
# BUG module, i.e. not initialized by BugInit.

from CvPythonExtensions import *
import BugPath
from configobj import ConfigObj
import os

# Parse as few files as necessary - to save time.
EARLY_ACCESS_CONFIG_FILES = ("bug main interface.ini", "bug advisors.ini")

class EarlyOptions:

	# BugPath isn't initialized yet and its methods for figuring out directories
	# won't work this early on. Will ultimately have to get the path from the DLL.
	def __init__(self, sConfigPath):
		self.configs = []
		sConfigPath = os.path.join(sConfigPath, BugPath.SETTINGS_FOLDER)
		if not os.path.isdir(sConfigPath):
			# Could just be the first launch of the mod. Let BUG handle the
			# config file creation once fully initialized.
			return
		for sFileName in os.listdir(sConfigPath):
			sFilePath = os.path.join(sConfigPath, sFileName)
			if os.path.isfile(sFilePath) and sFileName.lower() in EARLY_ACCESS_CONFIG_FILES:
				self.configs.append(ConfigObj(sFilePath, encoding='utf_8'))

	# These two based on IniFile in BugOptions.py
	def exists(self, config, section, key=None):
		return section in config and (key is None or key in config[section])

	def getValue(self, section__key, default=None):
		section, key = section__key.split("__", 1)
		for config in self.configs:
			if self.exists(config, section, key):
				val = config[section][key]
				# A little ad-hoc
				if str(val).lower() == "true":
					return 1
				if str(val).lower() == "false":
					return 0
				return int(val)
		return default
