General steps for internationalization:
1. To (re)extract translations from website: babel_extract.bat
2a. To create initial language-specific .po file:
	pybabel init -i messages.pot -d ../OpenAgua/translations -l xx (xx or xx_XX is the locale code). Note that Traditional and Simplified Chinese are zh_Hant and zh_Hans, respectively.
	Note: this should not be in a .bat, since it is just run once, and it is dangerous if it can be run accidentally.
2b. To update .po files:
	babel_update.bat
3. To compile .po files to .mo files for use in website:
	babel_compile.bat