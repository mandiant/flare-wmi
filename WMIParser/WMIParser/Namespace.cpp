#include "stdafx.h"
#include "Helper.h"
#include "Namespace.h"
#include "indexBTR.h"
#include "Hashing.h"

WMINamespaceClass::WMINamespaceClass(MappingFileClass &map) : Map(map), m_bXP(map.IsXPRepository()) {
}

WMINamespaceClass::~WMINamespaceClass() {
  Close();
}

void WMINamespaceClass::Close() {
  if (m_ObjFile != INVALID_HANDLE_VALUE) {
    ::CloseHandle(m_ObjFile);
    m_ObjFile = INVALID_HANDLE_VALUE;
  }
}

std::vector<std::wstring>* WMINamespaceClass::GetNamespaces() {
  return &NamespaceNames;
}

bool WMINamespaceClass::Init(const wchar_t *path) {
  HANDLE hFile = InitObjFile(path);
  if (hFile != INVALID_HANDLE_VALUE) {
    m_ObjFile = hFile;
    return true;
  }
  return false;
}

bool WMINamespaceClass::AddNamespaceRecord(std::string &strIn, NamespaceStruct& ns) {
  bool ret = false;
  std::string str;
  BuildSearchString(NAMESPACE_BASE_CLASS, str, m_bXP);
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      char* found = strstr(szIn, str.c_str());
      if (found) {
        char* strInstance = found + str.size();
        *found = 0;
        if (!SUCCEEDED(StringCbCopyA(ns.ParentNS, sizeof(ns.ParentNS), &szIn[3]))) {
          delete[] szIn;
          return false;
        }
        int index = 0;
        while (index < 3) {
          char *szDot = strrchr(strInstance, '.');
          if (!szDot)
            return false;
          char *val = szDot + 1;
          *szDot = 0;
          if (!index)
            ns.Size = atoll(val) & ALL_BITS_32;
          else if (1 == index)
            ns.RecordID = atoll(val) & ALL_BITS_32;
          else {
            ns.LogicalID = atoll(val) & ALL_BITS_32;
            if (!SUCCEEDED(StringCbCopyA(ns.InstanceNS, sizeof(ns.InstanceNS), &strInstance[3]))) {
              delete[] szIn;
              return false;
            }
          }
          index++;
        }
        ret = true;
      }
    }
    delete[] szIn;
  }
  return ret;
}

void WMINamespaceClass::BuildNSInstanceSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_<INSTANCE_NAME>.LogicalPage.RecordID.Size*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = NAMESPACE_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
}


void WMINamespaceClass::BuildSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP) {
  std::string strID;
  std::wstring strName(NAMESPACE_BASE_CLASS);
  GetStrId(strID, strName, bXP);
  szSearch = "\\";
  szSearch += INSTANCE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
}

bool WMINamespaceClass::ParseNamespaceRecords(const wchar_t *path) {
  if (Init(path)) {
    wchar_t rootNS[] = NAMESPACE_ROOT;
    DWORD i = 0;
    NamespaceNames.clear();
    NamespaceNames.push_back(rootNS);
    while (i < NamespaceNames.size()) {
      IndexBTR index(m_bXP);
      std::string strSearch;
      std::wstring wstrNamespace = NamespaceNames[i];
      BuildNSInstanceSearchString(wstrNamespace.c_str(), strSearch, m_bXP);
      if (index.SearchBTRFile(path, Map, strSearch)) {
        std::vector<std::string> *records = index.GetResults();
        if (records) {
          std::vector<std::string>::iterator it = records->begin();
          for (; it != records->end(); ++it) {
            NamespaceStruct nsStruct;
            if (AddNamespaceRecord(*it, nsStruct)) {
              std::wstring ns;
              if (ParseNSRecord(nsStruct, ns)) {
                std::wstring newns(NamespaceNames.at(i).c_str());
                newns += L"\\";
                newns += ns;
                NamespaceNames.push_back(newns);
              }
            }
          }
        }
      }
      i++;
    }
    return true;
  }
  return false;
}

bool WMINamespaceClass::ParseNSRecord(WMINamespaceClass::NamespaceStruct &rec, std::wstring &ns) {
  std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
  if (allocMap) {
    DWORD dwPhyPage = allocMap->at(rec.LogicalID);
    if (dwPhyPage != ALL_BITS_32)
      return FindRecord(dwPhyPage, rec.RecordID, rec.Size, ns);
  }
  return false;
}

bool WMINamespaceClass::FindRecord(DWORD dwPhyPage, DWORD dwRecordID, DWORD dwSize, std::wstring &ns) {
  LARGE_INTEGER offset;
  offset.QuadPart = dwPhyPage;
  offset.QuadPart *= PAGE_SIZE;
  BYTE page[PAGE_SIZE];
  if (INVALID_SET_FILE_POINTER != SetFilePointer(m_ObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
    DWORD justread = 0;
    if (::ReadFile(m_ObjFile, page, PAGE_SIZE, &justread, NULL) && PAGE_SIZE == justread) {
      const Toc* toc = reinterpret_cast<const Toc*>(page);
      const Toc* foundtoc = 0;
      while (!toc->IsZero()) {
        if (toc->IsValid(PAGE_SIZE)) {
          if (toc->RecordID == dwRecordID) {
            if (toc->Size != dwSize)
              wprintf(L"Size Mismatch : toc size = %.8X map size = %.8X\n", toc->Size, dwSize);
            foundtoc = toc;
            break;
          }
        }
        toc++;
      }
      if (foundtoc) {
        offset.QuadPart += foundtoc->Offset;
        if (INVALID_SET_FILE_POINTER != SetFilePointer(m_ObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
          BYTE *record = new BYTE[foundtoc->Size];
          if (record) {
            bool ret = false;
            if (::ReadFile(m_ObjFile, record, foundtoc->Size, &justread, NULL) && foundtoc->Size == justread) {
              if (foundtoc->Offset + foundtoc->Size <= PAGE_SIZE)
                ret = ParseNSRecord(record, foundtoc->Size, ns);
            }
            delete[] record;
            return ret;
          }
        }
      }
    }
  }
  return false;
}

bool WMINamespaceClass::ParseNSRecord(const BYTE *recordBuf, DWORD dwSize, std::wstring &ns) {
  const BYTE* parseBuf = recordBuf;
  const BYTE* endparseBuf = parseBuf + dwSize;
  wchar_t wszNamespace[] = NAMESPACE_BASE_CLASS;
  DWORD guidcount = m_bXP ? NS_MAX_STRING_XP_COUNT : NS_MAX_STRING_WIN7_COUNT;
  wchar_t wszGUIDStr[NS_MAX_STRING_WIN7_COUNT + 1];
  if (m_bXP)
    MD5Hash::GetStr(wszNamespace, wszGUIDStr, _countof(wszGUIDStr));
  else
    SHA256Hash::GetStr(wszNamespace, wszGUIDStr, _countof(wszGUIDStr));
  if (!_wcsnicmp(wszGUIDStr, reinterpret_cast<const wchar_t *>(parseBuf), guidcount)) {
    parseBuf += guidcount * sizeof(wchar_t);
    if (parseBuf + 2 * sizeof(uint64) < endparseBuf) { //two Dates 
      parseBuf += 2 * sizeof(uint64);
      DWORD remainingsize = 0;
      if (parseBuf + sizeof(DWORD) < endparseBuf) {
        remainingsize = *reinterpret_cast<const DWORD*>(parseBuf);
        if (parseBuf + remainingsize <= endparseBuf) {
          parseBuf += sizeof(DWORD);
          if (parseBuf + NS_BYTES_BYPASS < endparseBuf) {
            parseBuf += NS_BYTES_BYPASS;
            DWORD namespaceNameOff = *reinterpret_cast<const DWORD *>(parseBuf);
            if (parseBuf + sizeof(DWORD) < endparseBuf) {
              parseBuf += sizeof(DWORD);
              DWORD nextOff = *reinterpret_cast<const DWORD *>(parseBuf);
              if (parseBuf + nextOff < endparseBuf) {
                parseBuf += nextOff;
                if (parseBuf + sizeof(BYTE) < endparseBuf) {
                  parseBuf++;
                  DWORD dwDataSize = *reinterpret_cast<const DWORD *>(parseBuf);
                  dwDataSize &= 0x3FFFFFFF;
                  if (parseBuf + dwDataSize + sizeof(DWORD) <= endparseBuf) {
                    parseBuf += sizeof(DWORD);
                    if (parseBuf + namespaceNameOff < endparseBuf) {
                      const char *nsStr = reinterpret_cast<const char*>(parseBuf + namespaceNameOff + 1);
                      size_t len = strlen(nsStr);
                      if (len) {
                        if (wchar_t *wnsStr = new wchar_t[len + 1]) {
                          size_t retVal = 0;
                          bool ret = false;
                          if (!mbstowcs_s(&retVal, wnsStr, len + 1, nsStr, _TRUNCATE) && retVal) {
                            ns = wnsStr;
                            ret = true;
                          }
                          delete[] wnsStr;
                          return ret;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  return false;
}

void WMINamespaceClass::Print(const wchar_t *outlog) {
  FILE* out = CreateLogFile(outlog, L"at, ccs=UNICODE");
  MyPrintFunc(out, L"===============================Namespaces=========================\n");
  std::vector<std::wstring>::iterator it = NamespaceNames.begin();
  std::wstring strID;
  for (; it != NamespaceNames.end(); ++it) {
    GetWStrId(strID, *it, m_bXP);
    MyPrintFunc(out, L"%s (NS_%s)\n", it->c_str(), strID.c_str());
  }
  MyPrintFunc(out, L"==================================================================\n");
  if (out)
    ::fclose(out);
}
