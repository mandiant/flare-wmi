# recovering data from wmi repositories


in the event that objects are deleted from wmi repositories, it is sometimes feasible to recover them.
the techniques require a moderate knowledge of internal wmi structures; however, python-cim includes a number of scripts to ease the process.
generally, smaller objects are easier to recover than larger ones, and static classes easier to recover than class instances.

one scenario in which you might want to recover data is when dealing with a malicious actor that deploys wmi-resident malware.
the actor may store stolen data within the repository or host their malicious code in object properties.
we can use these data recovery techniques to extract forensic artifacts of an intrusion despite the wmi classes being deleted.

## strategy

  1. if you know *nothing* about the deleted data:
     1. carve class definitions from unallocated pages and slack spaces.
        you may recover complete classes and their static property values.
        now you are done!
        however, if the object overruns a single page (0x2000 bytes), this technique won't work.
        continue reading.
     2. carve metadata from unallocated pages and slack spaces and look for anomalies.
        the section on [dumping unused space](./dump-unused-space.md) discusses how to extract these raw bytes, while
        the tutorial on [carving class names](./tutorial-wmikatz.md) describes using tools that are purpose-built for carving from unused space.
        review the artifact timeline and correlate events with external activity.
        once you find interesting class or property names, continue with step (2).
     3. extract strings from unallocated pages and slack spaces and manually review.
        this includes hunting for terms that shouldn't exist in a wmi repository.
        see the section on [searching wmi repositories](./find-bytes.md) for a helpful wordlist.
     4. once you have identified suspicious artifacts, you can continue with step (2).
     5. if you can't find anything interesting, you're pretty much out of luck.
        i'm sorry.
  2. if you know something about the deleted data, continue here.
     this includes knowing: name of a property, class name, or fragment of a value.
     for example, you may be aware that an actor used a powershell-based backdoor, and therefore search for the powershell comment string `<#`.
     the [tutorial on ovewritten data](./tutorial-overwritten.md) describes this process in detail.
     1. use the `find_bytes.py` script to correlate string hits with structures within the wmi repository.
     2. review the structures containing hits. each one may be:
        1. an active object
        2. located in an unallocated page
        3. found in slack space
     3. parse the object and possibly recover property names and values.


## references:
  - [tutorial: overwritten objects](./tutorial-overwritten.md)
  - [tutorial: embedded backdoor](./tutorial-wmikatz.md)
  - [searching wmi repositories](./find-bytes.md)
  - [dumping unused regions](./dump-unused-space.md)
