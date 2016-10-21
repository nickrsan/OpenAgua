General steps for internationalization:
1. To (re)extract translations from website: babel_extract.bat
2a. To create initial language-specific .po file:
	babel_init_xx.bat (where xx is the language)
2b. To update .po files:
	babel_update.bat
3. To compile .po files to .mo files for use in website:
	babel_compile.bat