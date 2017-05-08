# searching for raw bytes across wmi repositories


you can search for bytes and/or strings in wmi repository structures using the `find_bytes.py` script.
for example, we can search for the string "testClass" (or encode it as hexadecimal: "74657374436c617373") by invoking the script like this:

```
$ python find_bytes.py . "testClass"
found hit on physical page 0x4b4 at offset 0x1b11
  mapped to logical page 0x680
  hit on object contents at entry index 0x9 id 0x67f759dd
  referred to by key NS_68577372C66A7B20658487FBD959AA154EF54B5F935DCC5663E9228B44322805/CD_92128A4E1ADC48BA9AA4C2DD8352632FEB34D1735315ACF5FDF17AE02CA83513.1664.1744263645.191
found hit on physical page 0x4ba at offset 0x1da9
  mapped to logical page 0x647
  hit in page slack space
found hit on physical page 0x4d5 at offset 0x1b11
  this page not mapped to a logical page (unallocated page)
```

for the first result, you can dump the object buffer using `dump_object.py . 1664.1744263645.191` or inspect it using the graphical repository browser.
for the remaining hits, you should review the physical page contents using `dump_page.py --addressing_mode physical . 0x4ba` (and page 0x4d5).
hex dumps of these pages can help you identify suspicious wmi repository objects, both active and deleted.


## fun search queries

here are some of the search terms that i like to use:

  - `<#`: the powershell block comment separator.
  - `==`: the base64 padding characters. also used in source code for the equality operator.
  - `TVqQAA`: the common MZ header `4D 5A 90 00` base64 encoded.
  - `ps1`: the powershell file extension.
  - `mattifestation`: the online persona for some hacker.
  - `zMzM`: `base64(hex(0xCC 0xCC))`. decodes to `int 3; int 3;` in x86 assembly. commonly used to pad functions to four-byte alignment in executables compiled with visual studio.

