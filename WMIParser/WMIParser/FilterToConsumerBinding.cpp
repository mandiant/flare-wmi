#include "stdafx.h"
#include "FilterToConsumerBinding.h"
#include "indexBTR.h"
#include "Hashing.h"

const wchar_t FilterToConsumerBindingClass::FILTER_TO_CONSUMER_BINDING_NAME[] = L"__FilterToConsumerBinding";

const ConsumerDataType FilterToConsumerBindingClass::FTCBDataTypes[FTCBDataTypesSize] = { // the order on disk
    { TS_STRING,    4, L"Filter" },
    { TS_STRING,    4, L"Consumer" },
    { TS_UINT32,    4, L"DeliveryQoS" },
    { TS_BOOLEAN,   2, L"DeliverSynchronously" },
    { TS_BOOLEAN,   2, L"MaintainSecurityContext" },
    { TS_BOOLEAN,   2, L"SlowDownProviders" },
    { TS_BYTEARRAY, 4, L"CreatorSID" }
};

FilterToConsumerBindingClass::FilterToConsumerBindingClass() : 
  ObjectHeaderClass(),
  Filter(),
  Consumer(),
  CreatorSID(),
  DeliveryQoS(),
  DeliverSynchronously(),
  MaintainSecurityContext(),
  SlowDownProviders()
{
}

FilterToConsumerBindingClass::FilterToConsumerBindingClass(const FilterToConsumerBindingClass &copyin) : 
  ObjectHeaderClass(copyin),
  Filter(copyin.Filter),
  Consumer(copyin.Consumer),
  CreatorSID(copyin.CreatorSID),
  DeliveryQoS(copyin.DeliveryQoS),
  DeliverSynchronously(copyin.DeliverSynchronously),
  MaintainSecurityContext(copyin.MaintainSecurityContext),
  SlowDownProviders(copyin.SlowDownProviders)
{
}

FilterToConsumerBindingClass::~FilterToConsumerBindingClass() {
}

void FilterToConsumerBindingClass::SetDeliverSynchronously(uint16 dataVal) {
  DeliverSynchronously = dataVal;
}

void FilterToConsumerBindingClass::SetMaintainSecurityContext(uint16 dataVal) {
  MaintainSecurityContext = dataVal;
}

void FilterToConsumerBindingClass::SetSlowDownProviders(uint16 dataVal) {
  SlowDownProviders = dataVal;
}

void FilterToConsumerBindingClass::SetDeliveryQoS(uint32 val) {
  DeliveryQoS = val;
}

void FilterToConsumerBindingClass::SetConsumer(uint64 s, uint64 c, int type) {
  Consumer.Set(s, c, type);
}

void FilterToConsumerBindingClass::SetConsumer(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Consumer.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Consumer.Set(extents, type);

}

void FilterToConsumerBindingClass::SetFilter(uint64 s, uint64 c, int type) {
  Filter.Set(s, c, type);
}

void FilterToConsumerBindingClass::SetFilter(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    Filter.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    Filter.Set(extents, type);
}

void FilterToConsumerBindingClass::SetCreatorSID(uint64 s, uint64 c) {
  CreatorSID.Set(s, c);
}

void FilterToConsumerBindingClass::SetCreatorSID(std::vector<ExtentClass>& extents) {
  if (extents.size() == 1)
    CreatorSID.Set(extents.at(0).GetStart(), extents.at(0).GetCount());
  else
    CreatorSID.Set(extents);
}

void FilterToConsumerBindingClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"\r\n===============================FilterToConsumer Binding======================\r\n");
  __super::Print(hFile, out);
  MyPrintFunc(out, L"Filter: ");
  Filter.Print(hFile, out);
  MyPrintFunc(out, L"Consumer: ");
  Consumer.Print(hFile, out);
  MyPrintFunc(out, L"CreatorSID: ");
  CreatorSID.Print(hFile, out);
  MyPrintFunc(out, L"DeliveryQoS: ");
  DeliveryQoS.Print(out);
  MyPrintFunc(out, L"DeliverSynchronously: ");
  DeliverSynchronously.Print(out);
  MyPrintFunc(out, L"MaintainSecurityContext: ");
  MaintainSecurityContext.Print(out);
  MyPrintFunc(out, L"SlowDownProviders: ");
  SlowDownProviders.Print(out);
  MyPrintFunc(out, L"\r\n=============================================================================\r\n");
}

FilterToConsumerBindingClass* FilterToConsumerBindingClass::Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, InstanceStruct &is, bool bXP) {
  std::vector<ExtentClass> consumerRecordExtents;
  if (is.Location.IsValid())
    if (!GetRecordExtents(hObjFile, allocMap, is.Location, consumerRecordExtents))
      return 0;
  return Create(hObjFile, consumerRecordExtents, is.Location.Size, bXP);
}

FilterToConsumerBindingClass* FilterToConsumerBindingClass::Create(HANDLE hObjFile, std::vector<ExtentClass>& cRecordExtents, DWORD cSize, bool bXP) {
  FilterToConsumerBindingClass* b = 0;
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
    if (currentIndex == cSize) {
      if (cRecordExtents.size()) {
        uint64 offset = cRecordExtents.at(0).GetStart();
        wprintf(L"FilterToConsumerBinding : Found the record at offset (%I64d)\r\n", offset);
      }
      b = Create(cRecordExtents, recBuf, cSize, bXP);
    }
    delete[] recBuf;
  }
  return b;
}

FilterToConsumerBindingClass* FilterToConsumerBindingClass::Create(std::vector<ExtentClass>& cRecordExtents, const void* recordBuf, uint32 size, bool bXP) {
  if (recordBuf && cRecordExtents.size() && size) {
    FilterToConsumerBindingClass * pObject = new FilterToConsumerBindingClass;
    if (pObject) {
      wchar_t wszGUIDStr[MAX_STRING_WIN7_COUNT + 1];
      if (bXP)
        MD5Hash::GetStr(FILTER_TO_CONSUMER_BINDING_NAME, wszGUIDStr, _countof(wszGUIDStr));
      else
        SHA256Hash::GetStr(FILTER_TO_CONSUMER_BINDING_NAME, wszGUIDStr, _countof(wszGUIDStr));
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

        uint32 tocSize = GetTocSize(FTCBDataTypes, FTCBDataTypesSize);
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
                    for (int i = 0; i < FTCBDataTypesSize; ++i) {
                      if (FTCBDataTypes[i].Type == TS_STRING) {
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
                                  if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"Filter"))
                                    pObject->SetFilter(ex, TS_STRING);
                                  else if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"Consumer"))
                                    pObject->SetConsumer(ex, TS_STRING);
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
                      else if (FTCBDataTypes[i].Type == TS_BYTEARRAY) {
                        if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"CreatorSID")) {
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
                      else if (FTCBDataTypes[i].Type == TS_UINT32) {
                        if (tocoffset + sizeof(uint32) <= endtocoffset) {
                          uint32 dataVal = *reinterpret_cast<const uint32*>(parseBuf + tocoffset);
                          if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"DeliveryQoS"))
                            pObject->SetDeliveryQoS(dataVal);
                          else
                            goto Exit;
                          tocoffset += sizeof(uint32);
                        }
                        else
                          goto Exit;
                      }
                      else if (FTCBDataTypes[i].Type == TS_BOOLEAN) {
                        if (tocoffset + sizeof(uint16) <= endtocoffset) {
                          uint16 dataVal = *reinterpret_cast<const uint16*>(parseBuf + tocoffset);
                          if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"DeliverSynchronously"))
                            pObject->SetDeliverSynchronously(dataVal);
                          else if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"MaintainSecurityContext"))
                            pObject->SetMaintainSecurityContext(dataVal);
                          else if (!_wcsicmp(FTCBDataTypes[i].ColumnName, L"SlowDownProviders"))
                            pObject->SetSlowDownProviders(dataVal);
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

FilterToConsumerBindingParserClass::FilterToConsumerBindingParserClass(MappingFileClass &map) : Map(map), m_bXP(map.IsXPRepository()) {
}

FilterToConsumerBindingParserClass::~FilterToConsumerBindingParserClass() {
  if (m_ObjFile != INVALID_HANDLE_VALUE)
    ::CloseHandle(m_ObjFile);
}

bool FilterToConsumerBindingParserClass::Init(const wchar_t *path) {
  HANDLE hFile = InitObjFile(path);
  if (hFile != INVALID_HANDLE_VALUE) {
    m_ObjFile = hFile;
    return true;
  }
  return false;
}

bool FilterToConsumerBindingParserClass::ParseAllBindings(const wchar_t* path, const wchar_t* szNamespace) {
  if (Init(path) && szNamespace) {
    IndexBTR index(m_bXP);
    std::string szSearch;
    BuildBindingInstanceSearchString(szNamespace, szSearch, m_bXP);
    if (index.SearchBTRFile(path, Map, szSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records && records->size()) {
        std::vector<std::string>::iterator it = records->begin();
        for (; it != records->end(); ++it) {
          InstanceStruct bs;
          ::memset(&bs, 0, sizeof(InstanceStruct));
          if (ConstructBindingRecord(*it, bs))
            AddBinding(bs);
        }
      }
      return true;
    }
  }
  return false;
}

bool FilterToConsumerBindingParserClass::ConstructBindingRecord(std::string &strIn, InstanceStruct &fs) {
  bool ret = false;
  std::string str;
  if (char * strInstance = new char[strIn.length() + 1]) {
    if (!strcpy_s(strInstance, strIn.length() + 1, strIn.c_str())) {
      int index = 0;
      while (index < 3) {
        char *szDot = strrchr(strInstance, '.');
        if (!szDot)
          goto Exit;
        char *val = szDot + 1;
        *szDot = 0;
        if (!index)
          fs.Location.Size = atoll(val) & ALL_BITS_32;
        else if (1 == index)
          fs.Location.RecordID = atoll(val) & ALL_BITS_32;
        else {
          fs.Location.LogicalID = atoll(val) & ALL_BITS_32;
        }
        index++;
      }
      char *szUnderscore = strrchr(strInstance, '_');
      if (!szUnderscore)
        goto Exit;
      if (!SUCCEEDED(StringCbCopyA(fs.InstanceID, sizeof(fs.InstanceID), szUnderscore + 1)))
        goto Exit;
      ret = true;
    }
  Exit:
    delete[] strInstance;
  }
  return ret;
}

void FilterToConsumerBindingParserClass::AddBinding(InstanceStruct& fs) {
  unsigned int index = 0;
  InstanceStruct* foundStruct = BinarySearchNS::BinarySearch<InstanceStruct, const char*>(Bindings, fs.InstanceID, CompareStringIDFunc, &index);
  if (!foundStruct) {
    std::vector<InstanceStruct>::iterator it = Bindings.begin();
    std::advance(it, index);
    Bindings.insert(it, fs);
  }
}

void FilterToConsumerBindingParserClass::BuildBindingInstanceSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_<INSTANCE_NAME>.LogicalPage.RecordID.Size
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = FILTERTOCONSUMER_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
}

void FilterToConsumerBindingParserClass::BuildBindingClassSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CR_<__EventConsumer>\C_
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_PREFIX;
  name = FILTERTOCONSUMER_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_SUB_PREFIX;
}

bool FilterToConsumerBindingParserClass::GetNewBindingClass(std::string& strIn, const wchar_t* szNamespace, std::string& szFilterClass, bool bXP) {
  std::string szSearch;
  bool ret = false;
  BuildBindingClassSearchString(szNamespace, szSearch, bXP);
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


void FilterToConsumerBindingParserClass::Print(const wchar_t* szNamespace, const wchar_t *outlog) {
  FILE* out = CreateLogFile(outlog, L"at, ccs=UNICODE");
  std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
  if (allocMap) {
    MyPrintFunc(out, L"==== FilterToConsumerBinding in namespace %s ====\n", szNamespace);
    std::vector<InstanceStruct>::iterator it = Bindings.begin();
    for (; it != Bindings.end(); ++it) {
      MyPrintFunc(out, L"[%S]:\nFilterToConsumerBinding:(%.8X.%.8X.%.8X)\n", it->InstanceID, it->Location.LogicalID, it->Location.RecordID, it->Location.Size);
      FilterToConsumerBindingClass* p = FilterToConsumerBindingClass::Create(m_ObjFile, *allocMap, *it, m_bXP);
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