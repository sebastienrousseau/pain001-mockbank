# SPDX-License-Identifier: Apache-2.0 OR MIT
# The README demo. Render with `make demo` (needs vhs); it runs the
# installed CLI and examples/upload_and_collect.py, which starts the
# bank on a loopback port with an ephemeral host key. Nothing leaves
# the machine and every value is synthetic.
Output .github/demo.gif

Set FontSize 14
Set Width 1200
Set Height 600
Set Padding 20
Set Theme "Catppuccin Mocha"

Type "pain001-mockbank --help"
Sleep 500ms
Enter
Sleep 2s

Type "python examples/upload_and_collect.py"
Sleep 500ms
Enter
Sleep 3s
