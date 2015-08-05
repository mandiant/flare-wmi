#include "stdafx.h"
#include "LogFileEventConsumer.h"
#include "Hashing.h"

const wchar_t LogFileEventConsumerClass::CONSUMER_NAME[] = L"LogFileEventConsumer";

const ConsumerDataType LogFileEventConsumerClass::ConsumerDataTypes[ConsumerDataTypesSize] = { // the order on disk
    { TS_STRING,    4, L"MachineName" },
    { TS_UINT32,    4, L"MaximumQueueSize" },
    { TS_BYTEARRAY, 4, L"CreatorSID" },
    { TS_STRING,    4, L"Name" },
    { TS_STRING,    4, L"Filename" },
    { TS_STRING,    4, L"Text" },
    { TS_UINT64,    8, L"MaximumFileSize" },
    { TS_BOOLEAN,   2, L"IsUnicode" }
};

bool LogFileEventConsumerClass::IsConsumer(const void* recordBuf, uint32 size, bool bXP) {
  wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
  if (bXP)
    MD5Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  else
    SHA256Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  return !_wcsnicmp(reinterpret_cast<const wchar_t*>(recordBuf), wszGUIDStr, wcslen(wszGUIDStr));
}

void LogFileEventConsumerClass::SetName(uint64 s, uint64 c, int type) {
  Name.Set(s, c, type);
}

void LogFileEventConsumerClass::SetName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Name.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Name.Set(extents, type);
}

void LogFileEventConsumerClass::SetFilename(uint64 s, uint64 c, int type) {
  FileName.Set(s, c, type);
}

void LogFileEventConsumerClass::SetFilename(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    FileName.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    FileName.Set(extents, type);
}

void LogFileEventConsumerClass::SetText(uint64 s, uint64 c, int type) {
  Text.Set(s, c, type);
}

void LogFileEventConsumerClass::SetText(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Text.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Text.Set(extents, type);
}


void LogFileEventConsumerClass::SetIsUnicode(uint16 value){
  IsUnicode.Set(value);
}

void LogFileEventConsumerClass::SetMaximumFileSize(uint64 dataVal) {
  MaximumFileSize = dataVal;
}

void LogFileEventConsumerClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"\r\n========================Log File Event Consumer=========================\r\n");
  EventConsumer::Print(hFile, out);
  MyPrintFunc(out, L"Name: ");
  Name.Print(hFile, out);
  MyPrintFunc(out, L"Filename: ");
  FileName.Print(hFile, out);
  MyPrintFunc(out, L"Text: ");
  Text.Print(hFile, out);
  MyPrintFunc(out, L"MaximumFileSize: ");
  MaximumFileSize.Print(out);
  MyPrintFunc(out, L"IsUnicode: ");
  IsUnicode.Print(out);
  MyPrintFunc(out, L"\r\n=============================================================================\r\n");
}

EventConsumer* LogFileEventConsumerClass::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP) {
  LogFileEventConsumerClass *pObject = 0;
  if (recordBuf && cRecordExtents.size() && size) {
    pObject = new LogFileEventConsumerClass;
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
        if (currentoffset + UNK_7_BYTES < size) {
          currentoffset += UNK_7_BYTES;
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
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Filename"))
                                    pObject->SetFilename(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Text"))
                                    pObject->SetText(ex, TS_STRING);
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
                      else if (ConsumerDataTypes[i].Type == TS_UINT32) {
                        if (tocoffset + sizeof(uint32) <= endtocoffset) {
                          uint32 dataVal = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"MaximumQueueSize"))
                            pObject->SetMaximumQueueSize(dataVal);
                          else
                            goto Exit;
                          tocoffset += sizeof(uint32);
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_UINT64) {
                        if (tocoffset + sizeof(uint64) <= endtocoffset) {
                          uint64 dataVal = *reinterpret_cast<const uint64*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"MaximumFileSize"))
                            pObject->SetMaximumFileSize(dataVal);
                          else
                            goto Exit;
                          tocoffset += sizeof(uint64);
                        }
                        else
                          goto Exit;
                      }
                      else if (ConsumerDataTypes[i].Type == TS_BOOLEAN) {
                        if (tocoffset + sizeof(uint16) <= endtocoffset) {
                          uint16 dataVal = *reinterpret_cast<const uint16*>(parseBuf + tocoffset);
                          if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"IsUnicode"))
                            pObject->SetIsUnicode(dataVal);
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
