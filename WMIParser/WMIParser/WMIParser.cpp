// WMIParser.cpp : Defines the entry point for the console application.
//
#include "stdafx.h"
#include "EventConsumer.h"
#include "indexBTR.h"
#include "Mapping.h"
#include "Hashing.h"
#include "Namespace.h"
#include "ConsumerParser.h"
#include "EventFilter.h"
#include "FilterToConsumerBinding.h"
#include "ClassDef.h"
#include "InstanceDec.h"

void ParseWMIDBFile(const wchar_t* path) {
  _TCHAR wszObjFile[MAX_PATH];
  bool bXP = false;
  if (_snwprintf_s(wszObjFile, MAX_PATH, _TRUNCATE, L"%s\\mapping.ver", path)) {
    HANDLE hVerFile = ::CreateFile(wszObjFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (INVALID_HANDLE_VALUE != hVerFile) {
      ::CloseHandle(hVerFile);
      bXP = true;
    }
  }

  if (_snwprintf_s(wszObjFile, MAX_PATH, _TRUNCATE, L"%s\\objects.data", path)) {
    HANDLE hFile = ::CreateFile(wszObjFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (INVALID_HANDLE_VALUE == hFile)
      return;
    LARGE_INTEGER fileSize;
    if (GetFileSizeEx(hFile, &fileSize) && fileSize.QuadPart) {
      LARGE_INTEGER currentoffset;
      byte         buffer[PAGE_SIZE + 1];
      uint32       toread = 0,
        page = 0;
      currentoffset.QuadPart = 0;
      buffer[PAGE_SIZE] = 0;
      while (currentoffset.QuadPart < fileSize.QuadPart) {
        int64  reminder = fileSize.QuadPart - currentoffset.QuadPart;
        DWORD  toread = reminder > PAGE_SIZE ? PAGE_SIZE : static_cast<DWORD>(reminder & ALL_BITS_32);
        DWORD  justread = 0;
        if (INVALID_SET_FILE_POINTER == SetFilePointer(hFile, currentoffset.LowPart, &currentoffset.HighPart, FILE_BEGIN))
          break;
        if (toread && ::ReadFile(hFile, buffer, toread, &justread, NULL) && toread == justread) {
          const Toc *toc = reinterpret_cast<const Toc*>(buffer);
          if (toc->IsValid(toread)) {
            const Toc	*lasttoc = reinterpret_cast<const Toc*>(&buffer[toc->Offset]),
              *prevToLas = lasttoc - 1;
            if (prevToLas->IsZero()) {
              //if (buffer[PAGE_SIZE - 1]) // interpret only the first page of multi-page record ... more research needed.
              //	buffer[PAGE_SIZE - 1] = 0;
              while (toc < prevToLas) {
                if (toc->IsValid(toread)) {
                  const unsigned char *bytes = reinterpret_cast<const unsigned char*>(toc);
                  std::vector<ExtentClass> extents;
                  ExtentClass e;
                  e.Set(currentoffset.QuadPart + toc->Offset, toc->Size);
                  extents.push_back(e);
                  EventConsumer* p = EventConsumer::Create(&buffer[toc->Offset], extents, toc->Size, bXP);
                  if (p) {
                    p->Print(hFile, 0);
                    delete p;
                  }
                }
                ++toc;
              }
            }
          }
        }
        else
          break;
        currentoffset.QuadPart += justread;
        ++page;
      }
    }
    ::CloseHandle(hFile);
  }
}

void BuildClassSearchString(const wchar_t* szNamespace, const wchar_t* szclass, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CD_<CLASSNAME>
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_DEF_PREFIX;
  name = szclass;
  GetStrId(strID, name, bXP);
  szSearch += strID;
}

bool ParseLocation(LocationStruct &ls, std::string &strIn) {
  bool ret = false;
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      int index = 0;
      while (index < 3) {
        char *szDot = strrchr(szIn, '.');
        if (!szDot)
          goto Exit;
        char *val = szDot + 1;
        *szDot = 0;
        if (!index)
          ls.Size = atoll(val) & ALL_BITS_32;
        else if (1 == index)
          ls.RecordID = atoll(val) & ALL_BITS_32;
        else
          ls.LogicalID = atoll(val) & ALL_BITS_32;
        index++;
      }
      ret = true;
    }
  Exit:
    delete[] szIn;
  }
  return ret;
}

void ParseIndexFile(const wchar_t* path, MappingFileClass &map) {
  IndexBTR index(map.IsXPRepository());
  std::string szSearch;
  BuildClassSearchString(L"root\\ccm", L"CCM_RecentlyUsedApps", szSearch, true);
  std::vector<DWORD> *allocMap = map.GetDataAllocMap();
  if (allocMap) {
    if (index.SearchBTRFile(path, map, szSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records) {
        std::vector<std::string>::iterator it = records->begin();
        for (; it != records->end(); ++it) {
          LocationStruct ls;
          wprintf(L"Class Win32_Service : %S\n", it->c_str());
          ParseLocation(ls, *it);
          DWORD dwPhyPage = allocMap->at(ls.LogicalID);
          wprintf(L"Class Win32_Service in Objects.data: Offset = %.8X size = %.8X RecordId = %.8X\n", dwPhyPage * PAGE_SIZE, ls.Size, ls.RecordID);
        }
      }
    }
  }
  //index.Print();
}

void ParseAllIndexFile(const wchar_t* path, MappingFileClass &map, const wchar_t *log = 0) {
  IndexBTR index(map.IsXPRepository());
  std::vector<std::string> szSearch;
  std::vector<DWORD> *allocMap = map.GetDataAllocMap();
  if (allocMap) {
    FILE *f = CreateLogFile(log, L"at, ccs=UNICODE");
    index.SearchBTRFile(path, map, szSearch, f);
    if (f)
      fclose(f);
  }
}

void ParseNamespace(const wchar_t* path, MappingFileClass &map, const wchar_t* logpath) {
  WMINamespaceClass ns(map);
  if (ns.ParseNamespaceRecords(path))
    ns.Print(logpath);
}

void CreateOutputLog(const wchar_t *path) {
  if (path && *path) {
    FILE *f = CreateLogFile(path, L"wt, ccs=UNICODE");
    if (f) {
      MyPrintFunc(f, L"Log Created : %s\r\n", path);
      ::fclose(f);
    }
    else
      wprintf_s(L"CreateOutputLog failed to create log file (%s)\r\n", path);
  }
}

void PrintCommand(const wchar_t *path, const wchar_t * cmd) {
  if (path && *path && cmd && *cmd) {
    FILE *f = CreateLogFile(path, L"at, ccs=UNICODE");
    if (f) {
      MyPrintFunc(f, L"\r\nCommand > %s\r\n", cmd);
      ::fclose(f);
    }
    else
      wprintf_s(L"PrintCommand failed to PrintCommand cmd (%s) to log file (%s)\r\n", cmd, path);
  }
}

int ReadCmdFromCin(wchar_t* cmd, size_t size) {
  wchar_t c;
  uint32 index = 0;
  while (index < size - 1) {
    c = getwchar();
    if (c == '\r' || c == '\n')
      break;
    cmd[index++] = c;
  } while (index < size && c != '\n');
  cmd[index] = 0;
  return index;
}

void PrintHelp() {
  wprintf(L"WMI Parser Help:\r\n");

  wprintf(L"--help\r\n");
  wprintf(L"  Hint: Print help.\r\n");

  wprintf(L"--quit\r\n");
  wprintf(L"  Hint: WMIParser quits.\r\n");

  wprintf(L"--namespaceinstance\r\n");
  wprintf(L"  Hint: Get all the namespaces defined in the repo.\r\n");

  wprintf(L"--instance namespacename [classname] [classinstancename]\r\n");
  wprintf(L"  Hint: Get the instance in the specified namespace by class and instance name.\r\n");

  wprintf(L"--consumerinstance namespacename [consumertype] [consumerinstancename]\r\n");
  wprintf(L"  Hint: Get the consumer instance in the specified namespace by type and name.\r\n");

  wprintf(L"--filterinstance namespacename [filterinstancename]\r\n");
  wprintf(L"  Hint: Get the filter instances in the specified namespace by name.\r\n");

  wprintf(L"--bindinginstance namespacename\r\n");
  wprintf(L"  Hint: Get all binding instances defined in the specified namespace.\r\n");

  wprintf(L"--classdef [namespacename] [classname]\r\n");
  wprintf(L"  Hint: Get the class definition in the specified namespace.\r\n");

  wprintf(L"--index\r\n");
  wprintf(L"  Hint: Print all the strings in index.btr.\r\n");
}

int _tmain(int argc, _TCHAR* argv[])
{
  if (!MD5Hash::Test())
    return 2;
  if (!SHA256Hash::Test())
    return 1;
  if (argc >= 3) {
    if (!_wcsicmp(argv[1], L"-p")) {
      const wchar_t *path = argv[2];
      const wchar_t *logpath = 0;
      if (argc > 4 && !_wcsicmp(argv[3], L"-o")) {
        logpath = argv[4];
        CreateOutputLog(logpath);
      }
      if (path && *path) {
        MappingFileClass map;
        int inner_argc = 0;
        if (map.Parse(path)) {
          wchar_t cmd[MAX_PATH];
          do {
            wprintf_s(L"Command > ");
            if (ReadCmdFromCin(cmd, _countof(cmd))) {
              PrintCommand(logpath, cmd);
              LPWSTR *inner_argv = CommandLineToArgvW(cmd, &inner_argc);
              if (inner_argc && inner_argv) {
                if (inner_argc > 3) {
                  if (!_wcsicmp(inner_argv[0], L"--consumerinstance")) { // --consumerinstance namespace type instancename
                    ConsumerParserClass cp(map);
                    if (cp.ParseConsumerInstance(path, inner_argv[1], inner_argv[2], inner_argv[3])) {
                      cp.Print(logpath, path, inner_argv[1], inner_argv[2], inner_argv[3]);
                    }
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--instance")) { //--instance namespace classname instancename
                    InstanceDeclarationParser instParser(path, inner_argv[1], map);
                    instParser.Parse(inner_argv[2], inner_argv[3], logpath);
                  }
                }
                else if (inner_argc > 2) {
                  if (!_wcsicmp(inner_argv[0], L"--consumerinstance")) { // --consumerinstance namespace type
                    ConsumerParserClass cp(map);
                    if (cp.ParseAllConsumersByType(path, inner_argv[1], inner_argv[2])) {
                      cp.Print(logpath, inner_argv[1], inner_argv[2]);
                    }
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--filterinstance")) { // --filterinstance namespace filtername
                    EventFilterParserClass fl(map);
                    if (fl.ParseFilterInstance(path, inner_argv[1], inner_argv[2])) {
                      fl.Print(logpath, inner_argv[1], inner_argv[2]);
                    }
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--classdef")) { //--classdef namespace classname
                    ClassDefinitionParser::Print(path, inner_argv[1], inner_argv[2], map, logpath);
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--instance")) { //--instance namespace classname
                    InstanceDeclarationParser instParser(path, inner_argv[1], map);
                    instParser.Parse(inner_argv[2], logpath);
                  }
                }
                else if (inner_argc > 1) {
                  if (!_wcsicmp(inner_argv[0], L"--classdef")) { //--classdef namespace
                    ClassDefinitionParser::Print(path, inner_argv[1], map, logpath);
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--consumerinstance")) { //--consumerinstance namespace
                    ConsumerParserClass cp(map);
                    if (cp.ParseAllConsumers(path, inner_argv[1])) {
                      cp.Print(logpath, inner_argv[1]);
                    }
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--filterinstance")) { //--filterinstance namespace
                    EventFilterParserClass fl(map);
                    if (fl.ParseAllFilterInstances(path, inner_argv[1])) {
                      fl.Print(logpath, inner_argv[1]);
                    }
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--bindinginstance")) { //--bindinginstance namespace
                    FilterToConsumerBindingParserClass bd(map);
                    if (bd.ParseAllBindings(path, inner_argv[1])) {
                      bd.Print(inner_argv[1], logpath);
                    }
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--instance")) { //--instance classname
                    InstanceDeclarationParser instParser(path, L"", map);
                    instParser.ParseInAllNS(inner_argv[1], logpath);
                  }
                }
                else if (inner_argc) {
                  if (!_wcsicmp(inner_argv[0], L"--namespaceinstance"))
                    ParseNamespace(path, map, logpath);
                  else if (!_wcsicmp(inner_argv[0], L"--classdef")) { //--classdef
                    ClassDefinitionParser::Print(path, map, logpath);
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--index")) {
                    ParseAllIndexFile(path, map, logpath);
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--help")) {
                    PrintHelp();
                  }
                  else if (!_wcsicmp(inner_argv[0], L"--quit"))
                    break;
                }
                else
                  break;
              }
            }
          } while (true);
        }
      }
    }
  }
  else
    wprintf(L"Usage : WMIParser.exe -p $path_to_objects_data$ [-o $output_file_path$]\r\n");
  return 0;
}
