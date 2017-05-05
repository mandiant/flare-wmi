# extracting used space from wmi repositories


## unallocated pages

the wmi repository allocates data in "pages", or sequences of 0x2000 bytes, that are mapped into a logical address space.
a page is marked as "unused" by removing it from the logical address space; however, the page is not overwritten, so we can often recover data from unallocated pages.
you can use `dump_unallocated_pages.py` to extract the bytes from unallocated data pages.
this is a great way to narrow down the search space when extracting strings for manual review.

example:
```
 $ python dump_unallocated_pages.py . | strings | grep "=="
INFO:__main__:found unallocated physical page: 0x48
INFO:__main__:found unallocated physical page: 0xd0
INFO:__main__:found unallocated physical page: 0x66f
INFO:__main__:found unallocated physical page: 0x674
INFO:__main__:found unallocated physical page: 0x675
                        #If SizeOfBlock == 0, we are done
INFO:__main__:found unallocated physical page: 0x677
INFO:__main__:found unallocated physical page: 0x67a
INFO:__main__:found unallocated physical page: 0x67c
INFO:__main__:found unallocated physical page: 0x67d
INFO:__main__:found unallocated physical page: 0x6d7
INFO:__main__:found unallocated physical page: 0x6d8
INFO:__main__:found unallocated physical page: 0x6d9
INFO:__main__:found unallocated physical page: 0x6da
Ii00w6EoJAABIjYwkkAAAAEiL0OjGlf//SIuUJJAAAABIjYwkmAAAAOixlf//SYvVQYvO...
INFO:__main__:found unallocated physical page: 0x6dc
INFO:__main__:found unallocated physical page: 0x6dd
INFO:__main__:found unallocated physical page: 0x6e5
INFO:__main__:found unallocated physical page: 0x6e7
```


## slack space

within an active page of data, there may be regions of unused data.
this is "slack" space.
while slack regions are typically much smaller in size than unallocated pages, they may still contain deleted objects.
you can use `dump_page_slack.py` to extract the bytes from the slack spaces.

example:
```
 $ python dump_page_slack.py . | strings | grep -i "privilege"
INFO:__main__:extracted 0x91 bytes of slack from logical page 0x0 at offset 0x1f6f
INFO:__main__:extracted 0x5f bytes of slack from logical page 0x2 at offset 0x1fa1
INFO:__main__:extracted 0x29 bytes of slack from logical page 0x5 at offset 0x1fd7
INFO:__main__:extracted 0x4b bytes of slack from logical page 0x6 at offset 0x1fb5
INFO:__main__:extracted 0x11 bytes of slack from logical page 0x7 at offset 0x1fef
INFO:__main__:extracted 0x65 bytes of slack from logical page 0x8 at offset 0x1f9b
INFO:__main__:extracted 0x53 bytes of slack from logical page 0x9 at offset 0x1fad
INFO:__main__:extracted 0x43 bytes of slack from logical page 0xa at offset 0x1fbd
INFO:__main__:extracted 0x5c bytes of slack from logical page 0xb at offset 0x1fa4
INFO:__main__:extracted 0xd bytes of slack from logical page 0xc at offset 0x1ff3
INFO:__main__:extracted 0x28 bytes of slack from logical page 0xd at offset 0x1fd8
INFO:__main__:extracted 0x3 bytes of slack from logical page 0xe at offset 0x1ffd
INFO:__main__:extracted 0x63 bytes of slack from logical page 0xf at offset 0x1f9d
Privileges
SeSecurityPrivilege
INFO:__main__:extracted 0xa bytes of slack from logical page 0x13 at offset 0x1ff6
INFO:__main__:extracted 0x35 bytes of slack from logical page 0x14 at offset 0x1fcb
INFO:__main__:extracted 0xb bytes of slack from logical page 0x15 at offset 0x1ff5
INFO:__main__:extracted 0x4a bytes of slack from logical page 0x16 at offset 0x1fb6
INFO:__main__:extracted 0x5 bytes of slack from logical page 0x17 at offset 0x1ffb
INFO:__main__:extracted 0x7c bytes of slack from logical page 0x18 at offset 0x1f84
INFO:__main__:extracted 0x41 bytes of slack from logical page 0x19 at offset 0x1fbf
INFO:__main__:extracted 0xf bytes of slack from logical page 0x1a at offset 0x1ff1
INFO:__main__:extracted 0x1b bytes of slack from logical page 0x1b at offset 0x1fe5
INFO:__main__:extracted 0x50 bytes of slack from logical page 0x1c at offset 0x1fb0
INFO:__main__:extracted 0x4a bytes of slack from logical page 0x1d at offset 0x1fb6
INFO:__main__:extracted 0xe bytes of slack from logical page 0x1e at offset 0x1ff2
INFO:__main__:extracted 0x7 bytes of slack from logical page 0x1f at offset 0x1ff9
INFO:__main__:extracted 0xd bytes of slack from logical page 0x20 at offset 0x1ff3
INFO:__main__:extracted 0x17 bytes of slack from logical page 0x21 at offset 0x1fe9
INFO:__main__:extracted 0x3a bytes of slack from logical page 0x22 at offset 0x1fc6
INFO:__main__:extracted 0x26 bytes of slack from logical page 0x23 at offset 0x1fda
INFO:__main__:extracted 0x35 bytes of slack from logical page 0x24 at offset 0x1fcb
INFO:__main__:extracted 0xbb bytes of slack from logical page 0x25 at offset 0x1f45
Win32API|AccessControl|Windows NT Privileges
PrivilegesRequired
Win32API|AccessControl|Windows NT Privileges
INFO:__main__:extracted 0xa bytes of slack from logical page 0x28 at offset 0x1ff6
```
