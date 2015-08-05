#include "stdafx.h"
#include "NTEventLogEventConsumer.h"
#include "Hashing.h"

const wchar_t NTEventLogEventConsumerClass::CONSUMER_NAME[] = L"NTEventLogEventConsumer";

const ConsumerDataType NTEventLogEventConsumerClass::ConsumerDataTypes[ConsumerDataTypesSize] = { // the order on disk
    { TS_STRING,      4,  L"MachineName" },
    { TS_UINT32,      4,  L"MaximumQueueSize" },
    { TS_BYTEARRAY,   4,  L"CreatorSID" },
    { TS_STRING,      4,  L"Name" },
    { TS_STRING,      4,  L"UNCServerName" },
    { TS_STRING,      4,  L"SourceName" },
    { TS_UINT32,      4,  L"EventID" },
    { TS_UINT32,      4,  L"EventType" },
    { TS_UINT16,      2,  L"Category" },
    { TS_UINT32,      4,  L"NumberOfInsertionStrings" },
    { TS_STRINGARRAY, 4,  L"InsertionStringTemplates" },
    { TS_STRING,      4,  L"NameOfRawDataProperty" },
    { TS_STRING,      4,  L"NameoftheUserSIDProp" },
};

bool NTEventLogEventConsumerClass::IsConsumer(const void* recordBuf, uint32 size, bool bXP) {
  wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
  if (bXP)
    MD5Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  else
    SHA256Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  return !_wcsnicmp(reinterpret_cast<const wchar_t*>(recordBuf), wszGUIDStr, wcslen(wszGUIDStr));
}

void NTEventLogEventConsumerClass::SetName(uint64 s, uint64 c, int type) {
  Name.Set(s, c, type);
}

void NTEventLogEventConsumerClass::SetName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Name.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Name.Set(extents, type);
}

void NTEventLogEventConsumerClass::SetUNCServerName(uint64 s, uint64 c, int type) {
  UNCServerName.Set(s, c, type);
}

void NTEventLogEventConsumerClass::SetUNCServerName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    UNCServerName.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    UNCServerName.Set(extents, type);
}

void NTEventLogEventConsumerClass::SetSourceName(uint64 s, uint64 c, int type) {
  SourceName.Set(s, c, type);
}

void NTEventLogEventConsumerClass::SetSourceName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    SourceName.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    SourceName.Set(extents, type);
}

void NTEventLogEventConsumerClass::SetNameOfRawDataProperty(uint64 s, uint64 c, int type) {
  NameOfRawDataProperty.Set(s, c, type);
}

void NTEventLogEventConsumerClass::SetNameOfRawDataProperty(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    NameOfRawDataProperty.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    NameOfRawDataProperty.Set(extents, type);
}

void NTEventLogEventConsumerClass::SetNameoftheUserSIDProp(uint64 s, uint64 c, int type) {
  NameoftheUserSIDProp.Set(s, c, type);
}

void NTEventLogEventConsumerClass::SetNameoftheUserSIDProp(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    NameoftheUserSIDProp.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    NameoftheUserSIDProp.Set(extents, type);
}

void NTEventLogEventConsumerClass::AddToInsertionStringTemplates(StringValue &str) {
  InsertionStringTemplates.Add(str);
}

void NTEventLogEventConsumerClass::SetEventID(uint32 val) {
  EventID = val;
}

void NTEventLogEventConsumerClass::SetEventType(uint32 val) {
  EventType = val;
}
void NTEventLogEventConsumerClass::SetNumberOfInsertionStrings(uint32 val) {
  NumberOfInsertionStrings = val;
}

void NTEventLogEventConsumerClass::SetCategory(uint16 val) {
  Category = val;
}

void NTEventLogEventConsumerClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"\r\n========================NT Event Log Event Consumer=========================\r\n");
  EventConsumer::Print(hFile, out);
  MyPrintFunc(out, L"Name: ");
  Name.Print(hFile, out);
  MyPrintFunc(out, L"Category: ");
  Category.Print(out);
  MyPrintFunc(out, L"EventID: ");
  EventID.Print(out);
  MyPrintFunc(out, L"EventType: ");
  EventType.Print(out);
  MyPrintFunc(out, L"InsertionStringTemplates: ");
  InsertionStringTemplates.Print(hFile, out);
  MyPrintFunc(out, L"NameOfRawDataProperty: ");
  NameOfRawDataProperty.Print(hFile, out);
  MyPrintFunc(out, L"NameOfUserSidProperty: ");
  NameoftheUserSIDProp.Print(hFile, out);
  MyPrintFunc(out, L"NumberOfInsertionStrings: ");
  NumberOfInsertionStrings.Print(out);
  MyPrintFunc(out, L"SourceName: ");
  SourceName.Print(hFile, out);
  MyPrintFunc(out, L"UNCServerName: ");
  UNCServerName.Print(hFile, out);
  MyPrintFunc(out, L"\r\n=============================================================================\r\n");
}

EventConsumer* NTEventLogEventConsumerClass::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP) {
  if (recordBuf && cRecordExtents.size() && size) {
    NTEventLogEventConsumerClass * pObject = new NTEventLogEventConsumerClass;
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
        if (currentoffset + UNK_9_BYTES < size) {
          currentoffset += UNK_9_BYTES;
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
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"UNCServerName"))
                                    pObject->SetUNCServerName(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"SourceName"))
                                    pObject->SetSourceName(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"NameOfRawDataProperty"))
                                    pObject->SetNameOfRawDataProperty(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"NameoftheUserSIDProp"))
                                    pObject->SetNameoftheUserSIDProp(ex, TS_STRING);
                                  else
                                    goto Exit;
                                }
                              }
                            }
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
                      else if (ConsumerDataTypes[i].Type == TS_STRINGARRAY) {
                        if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"InsertionStringTemplates")) {
                          if (tocoffset + sizeof(uint32) <= endtocoffset) {
                            uint32 indataoffset = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                            if (indataoffset) {
                              uint64 dataoffset = currentoffset + indataoffset;
                              if (dataoffset + sizeof(uint32) < size) { // first 4 bytes represent the size of the sid
                                const uint32 *stream = reinterpret_cast<const uint32*>(parseBuf + dataoffset);
                                uint32 count = *stream;
                                uint32 indatasize = (count + 1) * sizeof(uint32);
                                if (dataoffset + indatasize < size && indataoffset + indatasize <= datasize) {
                                  uint32 lastoffset = 0;
                                  ++stream;
                                  for (uint32 i = 0; i < count; ++i, ++stream) {
                                    if (currentoffset + *stream < size && *stream <= datasize) {
                                      uint32 strsize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(parseBuf + currentoffset + *stream + sizeof(byte))));
                                      if (*stream + strsize <= datasize) {
                                        std::vector<ExtentClass> ex;
                                        CreateFieldExtents(currentoffset + *stream + +sizeof(byte), strsize, cRecordExtents, ex);
                                        StringValue str(ex, TS_STRING);
                                        pObject->AddToInsertionStringTemplates(str);
                                      }
                                    }
                                    else
                                      break;
                                  }
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
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"EventID"))
                            pObject->SetEventID(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"EventType"))
                            pObject->SetEventType(dataVal);
                          else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"NumberOfInsertionStrings"))
                            pObject->SetNumberOfInsertionStrings(dataVal);
                          else
                            goto Exit;
                          tocoffset += sizeof(uint32);
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_UINT16) {
                        if (tocoffset + sizeof(uint16) <= endtocoffset) {
                          uint16 dataVal = *reinterpret_cast<const uint16*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Category"))
                            pObject->SetCategory(dataVal);
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
