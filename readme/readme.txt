Plugin for CudaText.
Gives command "Options Editor" which shows dialog for configuring all options in CudaText (they are listed in default.json, and are read/parsed from there by plugin).

By default saves options to user.json, but button "Target" can select "lexer override config" to save there. Options are grouped by sections, these sections are taken from default.json.

All options are shown in a table, after clicking any option you can see its default value, and change current value (or press "Reset" to change to default).
- For bool opts, checkbox is shown to change.
- For string/number opts, input is shown to change.
- For opts with limited count of values, combobox is shown, these are "enum_" values.
- For font-name opts, combobox is shown to change (it lists "default" font and all fonts installed in OS).

Also the button "Report" makes nice HTML report about current options. Report is opened in current Webbrowser. It does the same what plugin "Options Report" did, with small addition: it adds column for currently selected "target" lexer.


Author: Andrey Kvichanskiy (kvichans, at forum/github)
License: MIT
