#include "stdafx.h"
#include "CommandLineConsumer.h"
#include "Hashing.h"

const wchar_t CommandLineConsumerClass::CONSUMER_NAME[] = L"CommandLineEventConsumer";

const ConsumerDataType CommandLineConsumerClass::ConsumerDataTypes[ConsumerDataTypesSize] = { // the order on disk
    { TS_STRING,    4, L"MachineName" },
    { TS_UINT32,    4, L"MaximumQueueSize" },
    { TS_BYTEARRAY, 4, L"CreatorSID" },
    { TS_STRING,    4, L"Name" },
    { TS_STRING,    4, L"ExecutablePath" },
    { TS_STRING,    4, L"CommandLineTemplate" },
    { TS_BOOLEAN,   2, L"UseDefaultErrorMode" },
    { TS_BOOLEAN,   2, L"CreateNewConsole" },
    { TS_BOOLEAN,   2, L"CreateNewProcessGroup" },
    { TS_BOOLEAN,   2, L"CreateSeparateWowVdm" },
    { TS_BOOLEAN,   2, L"CreateSharedWowVdm" },
    { TS_SINT32,    4, L"Priority" },
    { TS_STRING,    4, L"WorkingDirectory" },
    { TS_STRING,    4, L"DesktopName" },
    { TS_STRING,    4, L"WindowTitle" },
    { TS_UINT32,    4, L"XCoordinate" },
    { TS_UINT32,    4, L"YCoordinate" },
    { TS_UINT32,    4, L"XSize" },
    { TS_UINT32,    4, L"YSize" },
    { TS_UINT32,    4, L"XNumCharacters" },
    { TS_UINT32,    4, L"YNumCharacters" },
    { TS_UINT32,    4, L"FillAttributes" },
    { TS_UINT32,    4, L"ShowWindowCommand" },
    { TS_BOOLEAN,   2, L"ForceOnFeedback" },
    { TS_BOOLEAN,   2, L"ForceOffFeedback" },
    { TS_BOOLEAN,   2, L"RunInteractively" },
    { TS_UINT32,    4, L"KillTimeout" }
};


bool CommandLineConsumerClass::IsConsumer(const void* recordBuf, uint32 size, bool bXP) {
  wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
  if (bXP)
    MD5Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  else
    SHA256Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  return !_wcsnicmp(reinterpret_cast<const wchar_t*>(recordBuf), wszGUIDStr, wcslen(wszGUIDStr));
}

void CommandLineConsumerClass::SetName(uint64 s, uint64 c, int type) {
  Name.Set(s, c, type);
}

void CommandLineConsumerClass::SetName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Name.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Name.Set(extents, type);
}

void CommandLineConsumerClass::SetExecutablePath(uint64 s, uint64 c, int type) {
  ExecutablePath.Set(s, c, type);
}

void CommandLineConsumerClass::SetExecutablePath(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    ExecutablePath.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    ExecutablePath.Set(extents, type);
}

void CommandLineConsumerClass::SetCommandLineTemplate(uint64 s, uint64 c, int type) {
  CommandLineTemplate.Set(s, c, type);
}

void CommandLineConsumerClass::SetCommandLineTemplate(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    CommandLineTemplate.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    CommandLineTemplate.Set(extents, type);
}

void CommandLineConsumerClass::SetWorkingDirectory(uint64 s, uint64 c, int type) {
  WorkingDirectory.Set(s, c, type);
}

void CommandLineConsumerClass::SetWorkingDirectory(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    WorkingDirectory.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    WorkingDirectory.Set(extents, type);
}

void CommandLineConsumerClass::SetDesktopName(uint64 s, uint64 c, int type) {
  DesktopName.Set(s, c, type);
}

void CommandLineConsumerClass::SetDesktopName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    DesktopName.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    DesktopName.Set(extents, type);
}

void CommandLineConsumerClass::SetWindowTitle(uint64 s, uint64 c, int type) {
  WindowTitle.Set(s, c, type);
}

void CommandLineConsumerClass::SetWindowTitle(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    WindowTitle.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    WindowTitle.Set(extents, type);
}

void CommandLineConsumerClass::SetKillTimeout(uint32 val) {
  KillTimeout = val;
}

void CommandLineConsumerClass::SetXCoordinate(uint32 val) {
  XCoordinate = val;
}
void CommandLineConsumerClass::SetYCoordinate(uint32 val) {
  YCoordinate = val;
}
void CommandLineConsumerClass::SetXSize(uint32 val) {
  XSize = val;
}
void CommandLineConsumerClass::SetYSize(uint32 val) {
  YSize = val;
}
void CommandLineConsumerClass::SetXNumCharacters(uint32 val) {
  XNumCharacters = val;
}
void CommandLineConsumerClass::SetYNumCharacters(uint32 val) {
  YNumCharacters = val;
}
void CommandLineConsumerClass::SetFillAttributes(uint32 val) {
  FillAttributes = val;
}
void CommandLineConsumerClass::SetShowWindowCommand(uint32 val) {
  ShowWindowCommand = val;
}
void CommandLineConsumerClass::SetPriority(sint32 dataVal) {
  Priority = dataVal;
}

void CommandLineConsumerClass::SetUseDefaultErrorMode(uint16 value) {
  UseDefaultErrorMode.Set(value);
}
void CommandLineConsumerClass::SetCreateNewConsole(uint16 value){
  CreateNewConsole.Set(value);
}
void CommandLineConsumerClass::SetCreateNewProcessGroup(uint16 value){
  CreateNewProcessGroup.Set(value);
}
void CommandLineConsumerClass::SetCreateSeparateWowVdm(uint16 value){
  CreateSeparateWowVdm.Set(value);
}
void CommandLineConsumerClass::SetCreateSharedWowVdm(uint16 value){
  CreateSharedWowVdm.Set(value);
}
void CommandLineConsumerClass::SetForceOnFeedback(uint16 value){
  ForceOnFeedback.Set(value);
}
void CommandLineConsumerClass::SetForceOffFeedback(uint16 value){
  ForceOffFeedback.Set(value);
}
void CommandLineConsumerClass::SetRunInteractively(uint16 value){
  RunInteractively.Set(value);
}

void CommandLineConsumerClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"\r\n========================Command Line Event Consumer=========================\r\n");
  EventConsumer::Print(hFile, out);
  MyPrintFunc(out, L"Name: ");
  Name.Print(hFile, out);
  MyPrintFunc(out, L"CommandLineTemplate: ");
  CommandLineTemplate.Print(hFile, out);
  MyPrintFunc(out, L"CreateNewConsole: ");
  CreateNewConsole.Print(out);
  MyPrintFunc(out, L"CreateNewProcessGroup: ");
  CreateNewProcessGroup.Print(out);
  MyPrintFunc(out, L"CreateSeparateWowVdm: ");
  CreateSeparateWowVdm.Print(out);
  MyPrintFunc(out, L"CreateSharedWowVdm: ");
  CreateSharedWowVdm.Print(out);
  MyPrintFunc(out, L"DesktopName: ");
  DesktopName.Print(hFile, out);
  MyPrintFunc(out, L"ExecutablePath: ");
  ExecutablePath.Print(hFile, out);
  MyPrintFunc(out, L"FillAttributes: ");
  FillAttributes.Print(out);
  MyPrintFunc(out, L"ForceOffFeedback: ");
  ForceOffFeedback.Print(out);
  MyPrintFunc(out, L"ForceOnFeedback: ");
  ForceOnFeedback.Print(out);
  MyPrintFunc(out, L"KillTimeout: ");
  KillTimeout.Print(out);
  MyPrintFunc(out, L"Priority: ");
  Priority.Print(out);
  MyPrintFunc(out, L"RunInteractively: ");
  RunInteractively.Print(out);
  MyPrintFunc(out, L"ShowWindowCommand: ");
  ShowWindowCommand.Print(out);
  MyPrintFunc(out, L"UseDefaultErrorMode: ");
  UseDefaultErrorMode.Print(out);
  MyPrintFunc(out, L"WindowTitle: ");
  WindowTitle.Print(hFile, out);
  MyPrintFunc(out, L"WorkingDirectory: ");
  WorkingDirectory.Print(hFile, out);
  MyPrintFunc(out, L"XCoordinate: ");
  XCoordinate.Print(out);
  MyPrintFunc(out, L"XNumCharacters: ");
  XNumCharacters.Print(out);
  MyPrintFunc(out, L"XSize: ");
  XSize.Print(out);
  MyPrintFunc(out, L"YCoordinate: ");
  YCoordinate.Print(out);
  MyPrintFunc(out, L"YNumCharacters: ");
  YNumCharacters.Print(out);
  MyPrintFunc(out, L"YSize: ");
  YSize.Print(out);
  MyPrintFunc(out, L"\r\n=============================================================================\r\n");
}

EventConsumer* CommandLineConsumerClass::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP) {
  if (recordBuf && cRecordExtents.size() && size) {
    CommandLineConsumerClass *pObject = new CommandLineConsumerClass;
    if (pObject) {
      wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
      if (bXP)
        MD5Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
      else
        SHA256Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
      uint32 guidsize = static_cast<uint32>(wcslen(wszGUIDStr) & ALL_BITS_32);
      uint64 currentoffset = 0;
      if (!_wcsnicmp(reinterpret_cast<const wchar_t*>(recordBuf), wszGUIDStr, guidsize)) {
        std::vector<ExtentClass> ex;
        guidsize *= sizeof(wchar_t);
        CreateFieldExtents(currentoffset, guidsize, cRecordExtents, ex);
        pObject->SetKnownGUID(ex, TS_USTRING);
        currentoffset += guidsize;
      }
      else
        goto Exit;
      if (currentoffset < size) {
        const BYTE* parseBuf = reinterpret_cast<const BYTE*>(recordBuf);
        if (currentoffset + sizeof(uint64) < size) {
          pObject->SetDate1(*reinterpret_cast<const uint64*>(parseBuf + currentoffset));
          currentoffset += sizeof(uint64);
        }
        else
          goto Exit;
        if (currentoffset + sizeof(uint64) < size) {
          pObject->SetDate2(*reinterpret_cast<const uint64*>(parseBuf + currentoffset));
          currentoffset += sizeof(uint64);
        }
        else
          goto Exit;

        uint32 remainingsize = 0;
        if (currentoffset + sizeof(uint32) < size) {
          remainingsize = *reinterpret_cast<const uint32*>(parseBuf + currentoffset);
          remainingsize &= 0x3FFFFFFF;
          if (currentoffset + remainingsize <= size)
            currentoffset += sizeof(uint32);
          else
            goto Exit;
        }
        else
          goto Exit;
        uint32 tocSize = GetTocSize(ConsumerDataTypes, ConsumerDataTypesSize);
        uint32 datasize = 0;
        if (currentoffset + UNK_C_BYTES < size) {
          currentoffset += UNK_C_BYTES;
          uint64 tocoffset = currentoffset;
          uint64 endtocoffset = tocoffset + tocSize;
          if (endtocoffset < size) {
            currentoffset += tocSize;
            uint32 nextSize = *reinterpret_cast<const uint32*>(parseBuf + currentoffset);
            if (currentoffset + nextSize < size) {
              currentoffset += nextSize;
              BYTE nextByteSize = *(parseBuf + currentoffset);
              if (currentoffset + nextByteSize < size) {
                currentoffset += nextByteSize;
                if (currentoffset + sizeof(uint32) < size) {
                  datasize = *reinterpret_cast<const uint32*>(parseBuf + currentoffset);
                  datasize &= 0x3FFFFFFF; // clearing the MSB (it is always set)
                  currentoffset += sizeof(uint32);
                  if (currentoffset + datasize <= size) {
                    for (int i = 0; i < ConsumerDataTypesSize; ++i) {
                      if (ConsumerDataTypes[i].Type == TS_STRING) {
                        if (tocoffset + sizeof(uint32) <= endtocoffset) {
                          uint32 indataoffset = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                          if (indataoffset) {
                            uint64 dataoffset = currentoffset + indataoffset;
                            if (dataoffset + sizeof(byte) < size) { // first byte of a string starts with a 0 byte
                              if (!*(parseBuf + dataoffset)) {
                                uint32 indatasize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(parseBuf + dataoffset + sizeof(byte))));
                                if (indataoffset + indatasize < datasize) {
                                  std::vector<ExtentClass> ex;
                                  CreateFieldExtents(dataoffset + sizeof(byte), indatasize, cRecordExtents, ex);
                                  if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"MachineName"))
                                    pObject->SetMachineName(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Name"))
                                    pObject->SetName(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"ExecutablePath"))
                                    pObject->SetExecutablePath(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CommandLineTemplate"))
                                    pObject->SetCommandLineTemplate(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"WorkingDirectory"))
                                    pObject->SetWorkingDirectory(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"DesktopName"))
                                    pObject->SetDesktopName(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"WindowTitle"))
                                    pObject->SetWindowTitle(ex, TS_STRING);
                                  else
                                    goto Exit;
                                }
                                else
                                  goto Exit;
                              }
                              else
                                goto Exit;
                            }
                            else
                              goto Exit;
                          }
                          tocoffset += sizeof(uint32);
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_BYTEARRAY) {
                        if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CreatorSID")) {
                          if (tocoffset + sizeof(uint32) <= endtocoffset) {
                            uint32 indataoffset = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                            if (indataoffset) {
                              uint64 dataoffset = currentoffset + indataoffset;
                              if (dataoffset + sizeof(uint32) < size) { // first 4 bytes represent the size of the sid
                                uint32 indatasize = *reinterpret_cast<const uint32*>(parseBuf + dataoffset);
                                indatasize += sizeof(uint32);
                                if (dataoffset + indatasize < size && indataoffset + indatasize <= datasize) {
                                  std::vector<ExtentClass> ex;
                                  CreateFieldExtents(dataoffset, indatasize, cRecordExtents, ex);
                                  pObject->SetCreatorSID(ex);
                                }
                                else
                                  goto Exit;
                              }
                              else
                                goto Exit;
                            }
                            tocoffset += sizeof(uint32);
                          }
                          else
                            goto Exit;
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_UINT32) {
                        if (tocoffset + sizeof(uint32) <= endtocoffset) {
                          uint32 dataVal = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"MaximumQueueSize"))
                            pObject->SetMaximumQueueSize(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"XCoordinate"))
                            pObject->SetXCoordinate(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"YCoordinate"))
                            pObject->SetYCoordinate(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"XSize"))
                            pObject->SetXSize(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"YSize"))
                            pObject->SetYSize(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"XNumCharacters"))
                            pObject->SetXNumCharacters(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"YNumCharacters"))
                            pObject->SetYNumCharacters(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"FillAttributes"))
                            pObject->SetFillAttributes(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"ShowWindowCommand"))
                            pObject->SetShowWindowCommand(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"KillTimeout"))
                            pObject->SetKillTimeout(dataVal);
                          else
                            goto Exit;
                          tocoffset += sizeof(uint32);
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_SINT32) {
                        if (tocoffset + sizeof(uint32) <= endtocoffset) {
                          sint32 dataVal = *reinterpret_cast<const sint32*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Priority")) {
                            if (dataVal)
                              pObject->SetPriority(dataVal);
                          }
                          else
                            goto Exit;
                          tocoffset += sizeof(sint32);
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_BOOLEAN) {
                        if (tocoffset + sizeof(uint16) <= endtocoffset) {
                          uint16 dataVal = *reinterpret_cast<const uint16*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"UseDefaultErrorMode"))
                            pObject->SetUseDefaultErrorMode(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CreateNewConsole"))
                            pObject->SetCreateNewConsole(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CreateNewProcessGroup"))
                            pObject->SetCreateNewProcessGroup(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CreateSeparateWowVdm"))
                            pObject->SetCreateSeparateWowVdm(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CreateSharedWowVdm"))
                            pObject->SetCreateSharedWowVdm(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"ForceOnFeedback"))
                            pObject->SetForceOnFeedback(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"ForceOffFeedback"))
                            pObject->SetForceOffFeedback(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"RunInteractively"))
                            pObject->SetRunInteractively(dataVal);
                          else
                            goto Exit;
                          tocoffset += sizeof(uint16);
                        }
                        else
                          goto Exit;
                      }
                    }
                    return pObject;
                  }
                }
              }
            }
          }
        }
      }
    Exit:
      delete pObject;
    }
  }
  return 0;
}
