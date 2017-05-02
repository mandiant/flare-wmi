import logging

from cim import CIM
from cim.objects import Namespace


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    Values = ["FolderPath", "ExplorerFileName", "FileSize", "LastUserName", "LastUsedTime", "TimeZoneOffset",
              "LaunchCount", "OriginalFileName", "FileDescription", "CompanyName", "ProductName", "ProductVersion",
              "FileVersion", "AdditionalProductCodes", "msiVersion", "msiDisplayName", "ProductCode",
              "SoftwarePropertiesHash", "ProductLanguage", "FilePropertiesHash", "msiPublisher"]
    print("\t".join(Values))

    c = CIM(type_, path)
    try:
        with Namespace(c, "root\\ccm\\SoftwareMeteringAgent") as ns:
            for RUA in ns.class_("CCM_RecentlyUsedApps").instances:
                RUAValues = []
                for Value in Values:
                    try:
                        if Value == "LastUsedTime":
                            Time = str(RUA.properties[Value].value)
                            ExcelTime = "{}-{}-{} {}:{}:{}".format(Time[0:4], Time[4:6], Time[6:8], Time[8:10],
                                                                   Time[10:12], Time[12:14])
                            RUAValues.append(ExcelTime)
                        elif Value == "TimeZoneOffset":
                            Time = str(RUA.properties[Value].value)
                            TimeOffset = '="{}"'.format(Time[-4:])
                            RUAValues.append(TimeOffset)
                        else:
                            RUAValues.append(str(RUA.properties[Value].value))
                    except KeyError:
                        RUAValues.append("")
                print("\t".join(RUAValues))
    except IndexError:
        raise RuntimeError("CCM Software Metering Agent path 'root\\\\ccm\\\\SoftwareMeteringAgent' not found.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    main(*sys.argv[1:])
