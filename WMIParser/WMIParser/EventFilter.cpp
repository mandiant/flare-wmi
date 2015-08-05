#include "stdafx.h"
#include "EventFilter.h"
#include "Hashing.h"
#include "indexBTR.h"

const wchar_t EventFilterClass::FILTER_NAME[] = L"__EventFilter";

const ConsumerDataType EventFilterClass::EFDataTypes[EFDataTypesSize] = { // the order on disk
    { TS_STRING,    4, L"Name" },
    { TS_BYTEARRAY, 4, L"CreatorSID" },
    { TS_STRING,    4, L"QueryLanguage" },
    { TS_STRING,    4, L"Query" },
    { TS_STRING,    4, L"EventNamespace" },
    { TS_UINT32,    4, L"EventAccess" }
};

EventFilterClass::EventFilterClass() :
  ObjectHeaderClass(),
  Name(),
  CreatorSID(),
  QueryLanguage(),
  Query(),
  EventNamespace(),
  EventAccess()
{
}

EventFilterClass::EventFilterClass(const EventFilterClass& copyin) :
  ObjectHeaderClass(copyin),
  Name(copyin.Name),
  CreatorSID(copyin.CreatorSID),
  QueryLanguage(copyin.QueryLanguage),
  Query(copyin.Query),
  EventNamespace(copyin.EventNamespace),
  EventAccess(copyin.EventAccess)
{
}

EventFilterClass::~EventFilterClass() {
}

void EventFilterClass::SetCreatorSID(uint64 s, uint64 c) {
  CreatorSID.Set(s, c);
}

void EventFilterClass::SetCreatorSID(std::vector<ExtentClass>& extents) {
  if (extents.size() == 1)
    CreatorSID.Set(extents.at(0).GetStart(), extents.at(0).GetCount());
  else
    CreatorSID.Set(extents);
}

void EventFilterClass::SetName(uint64 s, uint64 c, int type) {
  Name.Set(s, c, type);
}

void EventFilterClass::SetName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Name.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Name.Set(extents, type);
}

void EventFilterClass::SetQueryLanguage(uint64 s, uint64 c, int type) {
  QueryLanguage.Set(s, c, type);
}

void EventFilterClass::SetQueryLanguage(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    QueryLanguage.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    QueryLanguage.Set(extents, type);
}

void EventFilterClass::SetQuery(uint64 s, uint64 c, int type) {
  Query.Set(s, c, type);
}

void EventFilterClass::SetQuery(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Query.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Query.Set(extents, type);
}

void EventFilterClass::SetEventNamespace(uint64 s, uint64 c, int type) {
  EventNamespace.Set(s, c, type);
}

void EventFilterClass::SetEventNamespace(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    EventNamespace.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    EventNamespace.Set(extents, type);
}

void EventFilterClass::SetEventAccess(uint32 val) {
  EventAccess = val;
}

void EventFilterClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"\r\n===============================Event Filter=================================\r\n");
  __super::Print(hFile, out);
  MyPrintFunc(out, L"Name: ");
  Name.Print(hFile, out);
  MyPrintFunc(out, L"QueryLanguage: ");
  QueryLanguage.Print(hFile, out);
  MyPrintFunc(out, L"Query: ");
  Query.Print(hFile, out);
  MyPrintFunc(out, L"EventNamespace: ");
  EventNamespace.Print(hFile, out);
  MyPrintFunc(out, L"CreatorSID: ");
  CreatorSID.Print(hFile, out);
  MyPrintFunc(out, L"EventAccess: ");
  EventAccess.Print(out);
  MyPrintFunc(out, L"\r\n=============================================================================\r\n");
}

EventFilterClass* EventFilterClass::Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, InstanceStruct &fs, bool bXP) {
  std::vector<ExtentClass> consumerRecordExtents;
  if (fs.Location.IsValid())
    if (!GetRecordExtents(hObjFile, allocMap, fs.Location, consumerRecordExtents))
      return 0;
  return Create(hObjFile, consumerRecordExtents, fs.Location.Size, bXP);
}

EventFilterClass* EventFilterClass::Create(HANDLE hObjFile, std::vector<ExtentClass>& cRecordExtents, DWORD cSize, bool bXP) {
  EventFilterClass *ev = 0;
  BYTE *recBuf = new BYTE[cSize];
  if (recBuf) {
    std::vector<ExtentClass>::iterator it = cRecordExtents.begin();
    DWORD currentIndex = 0;
    DWORD justread = 0;
    for (; it != cRecordExtents.end(); ++it) {
      LARGE_INTEGER offset;
      offset.QuadPart = it->GetStart();
      if (INVALID_SET_FILE_POINTER != SetFilePointer(hObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
        DWORD toRead = static_cast<DWORD>(it->GetCount() & ALL_BITS_32);
        if (::ReadFile(hObjFile, recBuf + currentIndex, toRead, &justread, NULL) && toRead == justread) {
          currentIndex += toRead;
        }
        else
          break;
      }
      else
        break;
    }
    if (currentIndex == cSize)
      ev = Create(cRecordExtents, recBuf, cSize, bXP);
    delete[] recBuf;
  }
  return ev;
}

EventFilterClass* EventFilterClass::Create(std::vector<ExtentClass>& cRecordExtents, const void* recordBuf, uint32 size, bool bXP) {
  if (recordBuf && cRecordExtents.size() && size) {
    EventFilterClass * pObject = new EventFilterClass;
    if (pObject) {
      wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
      if (bXP)
        MD5Hash::GetStr(FILTER_NAME, wszGUIDStr, _countof(wszGUIDStr));
      else
        SHA256Hash::GetStr(FILTER_NAME, wszGUIDStr, _countof(wszGUIDStr));
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

        uint32 tocSize = GetTocSize(EFDataTypes, EFDataTypesSize);
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
                    for (int i = 0; i < EFDataTypesSize; ++i) {
                      if (EFDataTypes[i].Type == TS_STRING) {
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
                                  if (!_wcsicmp(EFDataTypes[i].ColumnName, L"Name"))
                                    pObject->SetName(ex, TS_STRING);
                                  else if (!_wcsicmp(EFDataTypes[i].ColumnName, L"QueryLanguage"))
                                    pObject->SetQueryLanguage(ex, TS_STRING);
                                  else if (!_wcsicmp(EFDataTypes[i].ColumnName, L"Query"))
                                    pObject->SetQuery(ex, TS_STRING);
                                  else if (!_wcsicmp(EFDataTypes[i].ColumnName, L"EventNamespace"))
                                    pObject->SetEventNamespace(ex, TS_STRING);
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
                      else if (EFDataTypes[i].Type == TS_BYTEARRAY) {
                        if (!_wcsicmp(EFDataTypes[i].ColumnName, L"CreatorSID")) {
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
                      else if (EFDataTypes[i].Type == TS_UINT32) {
                        if (tocoffset + sizeof(uint32) <= endtocoffset) {
                          uint32 dataVal = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                          if (!_wcsicmp(EFDataTypes[i].ColumnName, L"EventAccess"))
                            pObject->SetEventAccess(dataVal);
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

EventFilterParserClass::EventFilterParserClass(MappingFileClass &map) : Map(map), m_bXP(map.IsXPRepository()) {
}

EventFilterParserClass::~EventFilterParserClass() {
  if (m_ObjFile != INVALID_HANDLE_VALUE)
    ::CloseHandle(m_ObjFile);
}

bool EventFilterParserClass::Init(const wchar_t *path) {
  HANDLE hFile = InitObjFile(path);
  if (hFile != INVALID_HANDLE_VALUE) {
    m_ObjFile = hFile;
    return true;
  }
  return false;
}

void EventFilterParserClass::BuildFilterInstanceSearchString(const wchar_t* szNamespace, const wchar_t* szInst, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_<INSTANCE_NAME>.LogicalPage.RecordID.Size*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = FILTER_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
  name = szInst;
  GetStrId(strID, name, bXP);
  szSearch += strID;
}

void EventFilterParserClass::BuildAllFilterInstancesSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = FILTER_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
}

void EventFilterParserClass::BuildFilterClassSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CR_<__EventConsumer>\C_
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_PREFIX;
  name = FILTER_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_SUB_PREFIX;
}

bool EventFilterParserClass::GetNewFilterClass(std::string& strIn, const wchar_t* szNamespace, std::string& szFilterClass, bool bXP) {
  std::string szSearch;
  bool ret = false;
  BuildFilterClassSearchString(szNamespace, szSearch, bXP);
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      char* found = strstr(szIn, szSearch.c_str());
      if (found) {
        szFilterClass = found + szSearch.size();
        ret = true;
      }
    }
    delete[] szIn;
  }
  return ret;
}

bool EventFilterParserClass::ParseAllFilterInstances(const wchar_t* path, const wchar_t* szNamespace) {
  if (Init(path) && szNamespace) {
    IndexBTR index(m_bXP);
    std::string szSearch;
    BuildAllFilterInstancesSearchString(szNamespace, szSearch, m_bXP);
    if (index.SearchBTRFile(path, Map, szSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records && records->size()) {
        std::vector<std::string>::iterator it = records->begin();
        for (; it != records->end(); ++it) {
          InstanceStruct fs;
          ::memset(&fs, 0, sizeof(InstanceStruct));
          if (ConstructInstanceRecord(*it, fs))
            AddFilter(fs);
        }
      }
      return true;
    }
  }
  return false;
}

bool EventFilterParserClass::ParseFilterInstance(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szInstance) {
  if (Init(path) && szNamespace) {
    IndexBTR index(m_bXP);
    std::string strSearch;
    BuildFilterInstanceSearchString(szNamespace, szInstance, strSearch, m_bXP);
    if (index.SearchBTRFile(path, Map, strSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records && records->size() == 1) {
        InstanceStruct fs;
        ::memset(&fs, 0, sizeof(InstanceStruct));
        if (ConstructInstanceRecord(records->at(0), fs)) {
          AddFilter(fs);
          return true;
        }
      }
    }
  }
  return false;
}

void EventFilterParserClass::AddFilter(InstanceStruct& fs) {
  unsigned int index = 0;
  InstanceStruct* foundStruct = BinarySearchNS::BinarySearch<InstanceStruct, const char*>(Filters, fs.InstanceID, CompareStringIDFunc, &index);
  if (!foundStruct) {
    std::vector<InstanceStruct>::iterator it = Filters.begin();
    std::advance(it, index);
    Filters.insert(it, fs);
  }
}

void EventFilterParserClass::Print(const wchar_t *outlog, const wchar_t* szNamespace, const wchar_t* szInstance) {
  std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
  if (allocMap) {
    FILE* out = CreateLogFile(outlog, L"at, ccs=UNICODE");
    if (szInstance)
      MyPrintFunc(out, L"==== Filter %s\\__EventFilter\\%s ====\n", szNamespace, szInstance);
    else
      MyPrintFunc(out, L"==== Filters in namespace %s ====\n", szNamespace);
    std::vector<InstanceStruct>::iterator it = Filters.begin();
    for (; it != Filters.end(); ++it) {
      MyPrintFunc(out, L"[%S]:\nConsumer:(%.8X.%.8X.%.8X)\n", it->InstanceID, it->Location.LogicalID, it->Location.RecordID, it->Location.Size);
      EventFilterClass* p = EventFilterClass::Create(m_ObjFile, *allocMap, *it, m_bXP);
      if (p) {
        p->Print(m_ObjFile, out);
        delete p;
      }
    }
    MyPrintFunc(out, L"=============================================================================\n");
    if (out)
      ::fclose(out);
  }
}