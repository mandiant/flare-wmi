#include "stdafx.h"
#include "SMTPEventConsumer.h"
#include "Hashing.h"

const wchar_t SMTPEventConsumerClass::CONSUMER_NAME[] = L"SMTPEventConsumer";

const ConsumerDataType SMTPEventConsumerClass::ConsumerDataTypes[ConsumerDataTypesSize] = { // the order on disk
    { TS_STRING,      4,  L"MachineName" },
    { TS_UINT32,      4,  L"MaximumQueueSize" },
    { TS_BYTEARRAY,   4,  L"CreatorSID" },
    { TS_STRING,      4,  L"Name" },
    { TS_STRING,      4,  L"SMTPServer" },
    { TS_STRING,      4,  L"Subject" },
    { TS_STRING,      4,  L"FromLine" },
    { TS_STRING,      4,  L"ReplyToLine" },
    { TS_STRING,      4,  L"Message" },
    { TS_STRING,      4,  L"ToLine" },
    { TS_STRING,      4,  L"CcLine" },
    { TS_STRING,      4,  L"BccLine" },
    { TS_STRINGARRAY, 4,  L"HeaderFields" },
    
};

bool SMTPEventConsumerClass::IsConsumer(const void* recordBuf, uint32 size, bool bXP) {
  wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
  if (bXP)
    MD5Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  else
    SHA256Hash::GetStr(CONSUMER_NAME, wszGUIDStr, _countof(wszGUIDStr));
  return !_wcsnicmp(reinterpret_cast<const wchar_t*>(recordBuf), wszGUIDStr, wcslen(wszGUIDStr));
}

void SMTPEventConsumerClass::SetName(uint64 s, uint64 c, int type) {
  Name.Set(s, c, type);
}

void SMTPEventConsumerClass::SetName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Name.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Name.Set(extents, type);
}

void SMTPEventConsumerClass::SetSMTPServer(uint64 s, uint64 c, int type) {
  SMTPServer.Set(s, c, type);
}

void SMTPEventConsumerClass::SetSMTPServer(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    SMTPServer.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    SMTPServer.Set(extents, type);
}

void SMTPEventConsumerClass::SetSubject(uint64 s, uint64 c, int type) {
  Subject.Set(s, c, type);
}

void SMTPEventConsumerClass::SetSubject(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Subject.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Subject.Set(extents, type);
}

void SMTPEventConsumerClass::SetFromLine(uint64 s, uint64 c, int type) {
  FromLine.Set(s, c, type);
}

void SMTPEventConsumerClass::SetFromLine(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    FromLine.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    FromLine.Set(extents, type);
}

void SMTPEventConsumerClass::SetMessage(uint64 s, uint64 c, int type) {
  Message.Set(s, c, type);
}

void SMTPEventConsumerClass::SetMessage(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Message.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Message.Set(extents, type);
}

void SMTPEventConsumerClass::SetToLine(uint64 s, uint64 c, int type) {
  ToLine.Set(s, c, type);
}

void SMTPEventConsumerClass::SetToLine(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    ToLine.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    ToLine.Set(extents, type);
}

void SMTPEventConsumerClass::SetCcLine(uint64 s, uint64 c, int type) {
  CcLine.Set(s, c, type);
}

void SMTPEventConsumerClass::SetCcLine(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    CcLine.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    CcLine.Set(extents, type);
}

void SMTPEventConsumerClass::SetBccLine(uint64 s, uint64 c, int type) {
  BccLine.Set(s, c, type);
}

void SMTPEventConsumerClass::SetBccLine(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    BccLine.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    BccLine.Set(extents, type);
}

void SMTPEventConsumerClass::SetReplyToLine(uint64 s, uint64 c, int type) {
  ReplyToLine.Set(s, c, type);
}

void SMTPEventConsumerClass::SetReplyToLine(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    ReplyToLine.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    ReplyToLine.Set(extents, type);
}


void SMTPEventConsumerClass::AddToHeaderFields(StringValue &str) {
  HeaderFields.Add(str);
}


void SMTPEventConsumerClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"\r\n========================Log File Event Consumer=========================\r\n");
  EventConsumer::Print(hFile, out);
  MyPrintFunc(out, L"Name: ");
  Name.Print(hFile, out);
  MyPrintFunc(out, L"SMTPServer: ");
  SMTPServer.Print(hFile, out);
  MyPrintFunc(out, L"Subject: ");
  Subject.Print(hFile, out);
  MyPrintFunc(out, L"FromLine: ");
  FromLine.Print(hFile, out);
  MyPrintFunc(out, L"ReplyToLine: ");
  ReplyToLine.Print(hFile, out);
  MyPrintFunc(out, L"Message: ");
  Message.Print(hFile, out);
  MyPrintFunc(out, L"ToLine: ");
  ToLine.Print(hFile, out);
  MyPrintFunc(out, L"CcLine: ");
  CcLine.Print(hFile, out);
  MyPrintFunc(out, L"CcLine: ");
  CcLine.Print(hFile,out);
  MyPrintFunc(out, L"BccLine: ");
  BccLine.Print(hFile, out);
  MyPrintFunc(out, L"HeaderFields: ");
  HeaderFields.Print(hFile, out);
  MyPrintFunc(out, L"\r\n=============================================================================\r\n");
}

EventConsumer* SMTPEventConsumerClass::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP) {
  if (recordBuf && cRecordExtents.size() && size) {
    SMTPEventConsumerClass *pObject = new SMTPEventConsumerClass;
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
                        if (tocoffset + sizeof(uint32) < endtocoffset) {
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
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"SMTPServer"))
                                    pObject->SetSMTPServer(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Subject"))
                                    pObject->SetSubject(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"FromLine"))
                                    pObject->SetFromLine(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"ReplyToLine"))
                                    pObject->SetReplyToLine(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"Message"))
                                    pObject->SetMessage(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"ToLine"))
                                    pObject->SetToLine(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"CcLine"))
                                    pObject->SetCcLine(ex, TS_STRING);
                                  else if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"BccLine"))
                                    pObject->SetBccLine(ex, TS_STRING);
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
                          if (tocoffset + sizeof(uint32) < endtocoffset) {
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
                        if (!_wcsicmp(ConsumerDataTypes[i].ColumnName, L"HeaderFields")) {
                          if (tocoffset + sizeof(uint32) < endtocoffset) {
                            uint32 indataoffset = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                            if (indataoffset) {
                              uint64 dataoffset = currentoffset + indataoffset;
                              if (dataoffset + sizeof(uint32) < size) { // first 4 bytes represent the number of strings
                                const uint32 *stream = reinterpret_cast<const uint32*>(parseBuf + dataoffset);
                                uint32 count = *stream;
                                uint32 indatasize = (count + 1) * sizeof(uint32);
                                if (dataoffset + indatasize < size && indataoffset + indatasize <= datasize) {
                                  uint32 lastoffset = 0;
                                  ++stream;
                                  for (uint32 i = 0; i < count; ++i, ++stream) {
                                    if (currentoffset + *stream < size && *stream < datasize) {
                                      uint32 strsize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(parseBuf + currentoffset + *stream + sizeof(byte))));
                                      if (*stream + strsize <= datasize) {
                                        std::vector<ExtentClass> ex;
                                        CreateFieldExtents(currentoffset + *stream + sizeof(byte), strsize, cRecordExtents, ex);
                                        StringValue str(ex, TS_STRING);
                                        pObject->AddToHeaderFields(str);
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
                        if (tocoffset + sizeof(uint32) < endtocoffset) {
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