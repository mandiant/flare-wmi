#include "stdafx.h"
#include "indexBTR.h"
#include "Hashing.h"
#include "Helper.h"

IndexBTR::IndexBTR(bool bXP) : m_HFile(INVALID_HANDLE_VALUE), m_bXP(bXP) {
}

IndexBTR::~IndexBTR(){
  if (INVALID_HANDLE_VALUE != m_HFile)
    ::CloseHandle(m_HFile);
}

bool IndexBTR::NoCriteria(std::string& szIn, std::string &szSearch, bool bXP) {
  return true;
}

DWORD IndexBTR::GetRootPage(MappingFileClass &map) {
  if (m_bXP) {
    std::vector<DWORD> *alocMap = map.GetIndexAllocMap();
    if (alocMap) {
      DWORD page = alocMap->at(0);
      LARGE_INTEGER currentoffset;
      currentoffset.QuadPart = page;
      currentoffset.QuadPart *= PAGE_SIZE;
      if (INVALID_SET_FILE_POINTER != SetFilePointer(m_HFile, currentoffset.LowPart, &currentoffset.HighPart, FILE_BEGIN)) {
        PageHeader h;
        DWORD justread = 0;
        if (::ReadFile(m_HFile, &h, sizeof(h), &justread, NULL) && sizeof(h) == justread && h.IsAdmin())
          return h.XPRootPage;
      }
    }
  }
  else
    return map.GetIndexRootPage();
  return 0;

}

/*bool IndexBTR::SearchBTRFile(const wchar_t* path, MappingFileClass &map, std::vector<std::string> &aSearch) {
  _TCHAR wszIndexFile[MAX_PATH];
  if (_snwprintf_s(wszIndexFile, MAX_PATH, _TRUNCATE, L"%s\\index.btr", path)) {
    if (INVALID_HANDLE_VALUE == m_HFile)
      m_HFile = ::CreateFile(wszIndexFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (INVALID_HANDLE_VALUE == m_HFile)
      return false;
    LARGE_INTEGER fileSize;
    if (GetFileSizeEx(m_HFile, &fileSize) && fileSize.QuadPart) {
      DWORD index = 0;
      bool  ret = TRUE;
      for (; index < map.GetIndexAllocMap()->size(); ++index)
        ret &= ParseBTRPageWithCriteria(index, map.GetIndexAllocMap(), aSearch);
      return ret;
    }
  }
  return false;
}*/

bool IndexBTR::SearchBTRFile(const wchar_t* path, MappingFileClass &map, std::vector<std::string> &aSearch, FILE *out) {
  _TCHAR wszIndexFile[MAX_PATH];
  if (_snwprintf_s(wszIndexFile, MAX_PATH, _TRUNCATE, L"%s\\index.btr", path)) {
    if (INVALID_HANDLE_VALUE == m_HFile)
      m_HFile = ::CreateFile(wszIndexFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (INVALID_HANDLE_VALUE == m_HFile)
      return false;
    LARGE_INTEGER fileSize;
    if (GetFileSizeEx(m_HFile, &fileSize) && fileSize.QuadPart)
      return SearchBTRFile(GetRootPage(map), map.GetIndexAllocMap(), aSearch, out);
  }
  return false;
}

bool IndexBTR::SearchBTRFile(DWORD index, std::vector<DWORD> *alocMap, std::vector<std::string> &aSearch, FILE *out) {
  if (alocMap) {
    DWORD page = alocMap->at(index);
    if (ALL_BITS_32 == page)
      return TRUE;
    LARGE_INTEGER currentoffset;
    currentoffset.QuadPart = page;
    currentoffset.QuadPart *= PAGE_SIZE;
    if (INVALID_SET_FILE_POINTER == SetFilePointer(m_HFile, currentoffset.LowPart, &currentoffset.HighPart, FILE_BEGIN))
      return FALSE;
    byte  buf[PAGE_SIZE];
    DWORD justread = 0;
    if (::ReadFile(m_HFile, buf, PAGE_SIZE, &justread, NULL) && PAGE_SIZE == justread) {
      const PageHeader *h = reinterpret_cast<const PageHeader *>(buf);
      MyPrintFunc(out, L"Index %.8X - %.8X - %.8X - %.8X - %.8X\n", h->Sig, h->LogicalId, h->Zero1, h->XPRootPage, h->RecordCount);
      if (h->IsValid(index)) {
        std::string strIn;
        uint32 rec_count = reinterpret_cast<const PageHeader *>(buf)->RecordCount;
        if (rec_count) {
          const byte * start = reinterpret_cast<const byte *>(buf);
          const byte * curr = start + sizeof(PageHeader);
          const byte * end = start + PAGE_SIZE;
          uint32 ptrOffset = rec_count * sizeof(uint32);
          const uint32 *nextPage = reinterpret_cast<const uint32 *>(curr + ptrOffset);
          const uint32 *lastnextPage = nextPage + rec_count;
          uint32 afterPtrOffset = (rec_count + 1) * sizeof(uint32);
          const uint16 *toc = reinterpret_cast<const uint16 *>(curr + ptrOffset + afterPtrOffset);
          const uint16 *endtoc = toc + rec_count;
          const uint16 *intoNextTable = endtoc + 1;
          const uint16 *stringArray = toc + rec_count + 1 + *endtoc + 1;
          uint16 stringArraySize = toc[rec_count + *endtoc + 1];
          uint16 afterStringsOff = stringArray[stringArraySize];
          const char *strings = reinterpret_cast<const char *>(stringArray + stringArraySize + 1);
          DWORD val = 0;
          for (; val <= rec_count; ++val)
            MyPrintFunc(out, L"Next : %.8X - %.8X\n", val, nextPage[val]);
          val = 0;
          while (toc < endtoc) {
            uint16 toc_count = intoNextTable[*toc];
            bool composed = true;
            bool bNamespace = false;
            for (int i = 1; i <= toc_count; ++i) {
              uint16 offInStringOffArray = intoNextTable[*toc + i];
              if (offInStringOffArray < stringArraySize) {
                uint16 stroff = stringArray[offInStringOffArray];
                if (stroff < afterStringsOff) {
                  if (i == 1)
                    strIn = &strings[stroff];
                  else {
                    strIn += "\\";
                    strIn += &strings[stroff];
                  }
                }
              }
            }
            if (!aSearch.size())
              MyPrintFunc(out, L"%.8X -> %S\n", val, strIn.c_str());
            else {
              std::vector<std::string>::iterator it = aSearch.begin();
              for (; it != aSearch.end(); ++it) {
                std::string::size_type pos = strIn.find(*it);
                if (pos != std::string::npos) {
                  m_aResult.push_back(strIn);
                  break;
                }
              }
            }
            toc++;
            val++;
          }
          bool ret = true;
          while (nextPage <= lastnextPage) {
            DWORD leafval = m_bXP ? 0 : ALL_BITS_32;
            if (*nextPage != leafval)
              ret &= SearchBTRFile(*nextPage, alocMap, aSearch, out);
            nextPage++;
          }
          return ret;
        }
      }
      else if (h->IsAdmin() || h->IsDeleted())
        return true;
    }
  }
  return false;
}

bool IndexBTR::SearchBTRFile(const wchar_t* path, MappingFileClass &map, std::string &strSearch) {
  if (strSearch.length()) {
    _TCHAR wszIndexFile[MAX_PATH];
    m_aResult.clear();
    if (_snwprintf_s(wszIndexFile, MAX_PATH, _TRUNCATE, L"%s\\index.btr", path)) {
      if (INVALID_HANDLE_VALUE == m_HFile)
        m_HFile = ::CreateFile(wszIndexFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
      if (INVALID_HANDLE_VALUE == m_HFile)
        return false;
      LARGE_INTEGER fileSize;
      if (GetFileSizeEx(m_HFile, &fileSize) && fileSize.QuadPart)
        return SearchBTRFile(GetRootPage(map), map.GetIndexAllocMap(), strSearch);
    }
  }
  return false;
}

bool IndexBTR::SearchBTRFile(DWORD logpage, std::vector<DWORD> *alocMap, std::string &strSearch) {
  if (alocMap) {
    DWORD page = alocMap->at(logpage);
    if (ALL_BITS_32 == page)
      return TRUE;
    LARGE_INTEGER currentoffset;
    currentoffset.QuadPart = page;
    currentoffset.QuadPart *= PAGE_SIZE;
    if (INVALID_SET_FILE_POINTER == SetFilePointer(m_HFile, currentoffset.LowPart, &currentoffset.HighPart, FILE_BEGIN))
      return FALSE;
    byte  buf[PAGE_SIZE];
    DWORD justread = 0;
    if (::ReadFile(m_HFile, buf, PAGE_SIZE, &justread, NULL) && PAGE_SIZE == justread) {
      const PageHeader *h = reinterpret_cast<const PageHeader *>(buf);
      if (h->IsValid(logpage)) {
        std::string strIn;
        uint32 rec_count = reinterpret_cast<const PageHeader *>(buf)->RecordCount;
        if (rec_count) {
          const byte * start = reinterpret_cast<const byte *>(buf);
          const byte * curr = start + sizeof(PageHeader);
          const byte * end = start + PAGE_SIZE;
          uint32 ptrOffset = rec_count * sizeof(uint32);
          const uint32 *nextPage = reinterpret_cast<const uint32 *>(curr + ptrOffset);
          const uint32 *lastnextPage = nextPage + rec_count;
          uint32 afterPtrOffset = (rec_count + 1) * sizeof(uint32);
          const uint16 *toc = reinterpret_cast<const uint16 *>(curr + ptrOffset + afterPtrOffset);
          const uint16 *endtoc = toc + rec_count;
          const uint16 *intoNextTable = endtoc + 1;
          const uint16 *stringArray = toc + rec_count + 1 + *endtoc + 1;
          uint16 stringArraySize = toc[rec_count + *endtoc + 1];
          uint16 afterStringsOff = stringArray[stringArraySize];
          const char *strings = reinterpret_cast<const char *>(stringArray + stringArraySize + 1);
          DWORD index = 0;
          std::vector<DWORD> nextpages;
          while (toc < endtoc) {
            uint16 toc_count = intoNextTable[*toc];
            bool bNamespace = false;
            for (int i = 1; i <= toc_count; ++i) {
              uint16 offInStringOffArray = intoNextTable[*toc + i];
              if (offInStringOffArray < stringArraySize) {
                uint16 stroff = stringArray[offInStringOffArray];
                if (stroff < afterStringsOff) {
                  if (i == 1)
                    strIn = &strings[stroff];
                  else {
                    strIn += "\\";
                    strIn += &strings[stroff];
                  }
                }
              }
            }
            int result = strIn.compare(0, strSearch.length(), strSearch);
            if (!result) {
              m_aResult.push_back(strIn);
              nextpages.push_back(index);
              index++;
            }
            else if (result < 0)
              index++;
            else {
              nextpages.push_back(index);
              break;
            }
            toc++;
          }
          bool ret = true;
          if (!nextpages.size())
            nextpages.push_back(rec_count);
          std::vector<DWORD>::iterator pageit = nextpages.begin();
          for (; pageit != nextpages.end(); ++pageit) {
            if (index <= rec_count) {
              DWORD leafval = m_bXP ? 0 : ALL_BITS_32;
              if (nextPage[*pageit] != leafval)
                ret &= SearchBTRFile(nextPage[*pageit], alocMap, strSearch);
            }
          }
          return ret;
        }
      }
      else if (h->IsAdmin() || h->IsDeleted())
        return true;
    }
  }
  return false;
}


void IndexBTR::Print(const wchar_t* outlog) {
  FILE *f = CreateLogFile(outlog, L"at, ccs=UNICODE");
  std::vector<std::string>::iterator it = m_aResult.begin();
  for (; it != m_aResult.end(); ++it) {
    MyPrintFunc(f, L"%S\n", it->c_str());
  }
  if (f)
    fclose(f);
}