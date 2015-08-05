#include "stdafx.h"
#include "Mapping.h"

// To Do ... 
// ************************************************
// Win7 -> validate CRC of the page in Objects.data
//*************************************************
MappingFileClass::MappingFileClass() :
  m_hMappingHandle(INVALID_HANDLE_VALUE),
  m_dwIndexRootPage(0),
  m_bCleanShutdown(false), 
  m_bXPRepository(false) 
{
}

MappingFileClass::~MappingFileClass() {}

bool MappingFileClass::FindCurrentMappingFile(LPCTSTR szFolder) {
  _TCHAR wszMappingFile[MAX_PATH];
  HANDLE hMappingHandles[MAX_MAPPING_FILES] = { INVALID_HANDLE_VALUE, INVALID_HANDLE_VALUE, INVALID_HANDLE_VALUE };
  DWORD  dwMappingFileCount = MAX_MAPPING_FILES;
  int len = _snwprintf_s(wszMappingFile, MAX_PATH, _TRUNCATE, L"%s\\Mapping.ver", szFolder);
  if (len && len < MAX_PATH) {
    HANDLE hFile = ::CreateFile(wszMappingFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile != INVALID_HANDLE_VALUE) {
      m_bXPRepository = true;
      ::CloseHandle(hFile);
    }
  }

  for (int i = 0; i < MAX_MAPPING_FILES; ++i) {
    len = _snwprintf_s(wszMappingFile, MAX_PATH, _TRUNCATE, L"%s\\Mapping%d.map", szFolder, i + 1);
    if (len && len < MAX_PATH) {
      hMappingHandles[i] = ::CreateFile(wszMappingFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
      if (hMappingHandles[i] == INVALID_HANDLE_VALUE) {
        dwMappingFileCount = i;
        break;
      }
    }
  }
  DWORD maxVersion = 0;
  DWORD ii = 0;
  int   index = -1;
  for (; ii < dwMappingFileCount; ++ii) {
    DWORD version = 0;
    if (ReadVersion(hMappingHandles[ii], version)) {
      if (version > maxVersion) {
        maxVersion = version;
        index = ii;
      }
      else
        break;
    }
  }
  ii = 0;
  for (; ii < dwMappingFileCount; ++ii) {
    if (ii == index) {
      m_hMappingHandle = hMappingHandles[ii];
    }
    else
      ::CloseHandle(hMappingHandles[ii]);
  }
  return m_hMappingHandle != INVALID_HANDLE_VALUE;
}

bool MappingFileClass::ReadVersion(HANDLE hMappingFile, DWORD &version) {
  version = 0;
  LARGE_INTEGER fileSize;
  if (GetFileSizeEx(hMappingFile, &fileSize) && fileSize.QuadPart > sizeof(MappingHeader)) {
    LARGE_INTEGER zeroOffset;
    zeroOffset.QuadPart = 0;
    if (INVALID_SET_FILE_POINTER != SetFilePointer(hMappingFile, zeroOffset.LowPart, &zeroOffset.HighPart, FILE_BEGIN)) {
      MappingHeader header;
      DWORD         justread = 0;
      if (::ReadFile(hMappingFile, &header, sizeof(header), &justread, NULL) && sizeof(header) == justread && header.IsValid()) {
        version = header.dwVersion;
        return true;
      }
    }
  }
  return false;
}


bool MappingFileClass::ParseMappingRecords(std::vector<DWORD> *aPhyDataPages, std::vector<DWORD> *aFreePages, DWORD& offset, DWORD filesize) {
  if (aPhyDataPages && aFreePages) {
    DWORD justread = 0;
    DWORD id = 0;
    DWORD l_dwMappingEntries = 0;
    DWORD l_dwPhysicalPages = 0;
    if (m_bXPRepository) {
      if (filesize > sizeof(MappingXPHeader)) {
        MappingXPHeader header;
        if (::ReadFile(m_hMappingHandle, &header, sizeof(MappingXPHeader), &justread, NULL) && sizeof(MappingXPHeader) == justread && header.IsValid()) {
          l_dwMappingEntries = header.dwMappingEntries;
          l_dwPhysicalPages = header.dwPhysicalPages;
        }
      }
    }
    else if (filesize > sizeof(MappingWin7Header)) {
      MappingWin7Header header;
      if (::ReadFile(m_hMappingHandle, &header, sizeof(MappingWin7Header), &justread, NULL) && sizeof(MappingWin7Header) == justread && header.IsValid()) {
        l_dwMappingEntries = header.dwMappingEntries;
        l_dwPhysicalPages = header.dwPhysicalPages;
        id = header.dwFirstID;
      }
    }
    if (l_dwMappingEntries && l_dwPhysicalPages) {
      offset += justread;
      if (offset < filesize) {
        if (m_bXPRepository) {
          if (offset + l_dwMappingEntries * sizeof(DWORD) < filesize) {
            for (DWORD i = 0; i < l_dwMappingEntries; ++i) {
              DWORD dwphyPage = 0;
              if (::ReadFile(m_hMappingHandle, &dwphyPage, sizeof(DWORD), &justread, NULL) && justread == sizeof(DWORD)) {
                if (MAPPING_PAGE_UNAVAIL != dwphyPage) {
                  dwphyPage &= MAPPING_PAGE_ID_MASK;
                  if (dwphyPage >= l_dwPhysicalPages)
                    dwphyPage = MAPPING_PAGE_UNAVAIL;
                }
              }
              else
                dwphyPage = MAPPING_PAGE_UNAVAIL;
              aPhyDataPages->push_back(dwphyPage);
            }
            offset += l_dwMappingEntries * sizeof(DWORD);
          }
          else
            return false;
        }
        else if (offset + l_dwMappingEntries * sizeof(MappingOnDiskEntry) < filesize) {
          for (DWORD i = 0; i < l_dwMappingEntries; ++i) {
            MappingOnDiskEntry dwphyPageEntry;
            DWORD dwphyPage = MAPPING_PAGE_UNAVAIL;
            if (::ReadFile(m_hMappingHandle, &dwphyPageEntry, sizeof(MappingOnDiskEntry), &justread, NULL) && justread == sizeof(MappingOnDiskEntry) && id == dwphyPageEntry.dwFirstID) {
              if (!i)
                m_dwIndexRootPage = dwphyPageEntry.dwUserData;
              dwphyPage = dwphyPageEntry.dwPageNumber;
              if (MAPPING_PAGE_UNAVAIL != dwphyPage) {
                dwphyPage &= MAPPING_PAGE_ID_MASK;
                if (dwphyPage >= l_dwPhysicalPages)
                  dwphyPage = MAPPING_PAGE_UNAVAIL;
              }
            }
            aPhyDataPages->push_back(dwphyPage);
          }
          offset += l_dwMappingEntries * sizeof(MappingOnDiskEntry);
        }
        else
          return false;
        if (offset + sizeof(DWORD) < filesize) {
          DWORD dwfreePages = 0;
          offset += sizeof(DWORD);
          if (::ReadFile(m_hMappingHandle, &dwfreePages, sizeof(DWORD), &justread, NULL) && justread == sizeof(DWORD)) {
            if (offset + dwfreePages * sizeof(DWORD) < filesize) {
              for (DWORD i = 0; i < dwfreePages; ++i) {
                DWORD dwfreephyPage = 0;
                if (::ReadFile(m_hMappingHandle, &dwfreephyPage, sizeof(DWORD), &justread, NULL) && justread == sizeof(DWORD)) {
                  if (MAPPING_PAGE_UNAVAIL != dwfreephyPage)
                    dwfreephyPage &= MAPPING_PAGE_ID_MASK;
                }
                else
                  dwfreephyPage = MAPPING_PAGE_UNAVAIL;
                aFreePages->push_back(dwfreephyPage);

              }
              offset += dwfreePages * sizeof(DWORD);
              if (offset + sizeof(DWORD) < filesize){
                DWORD dwEndSig = 0;
                if (::ReadFile(m_hMappingHandle, &dwEndSig, sizeof(DWORD), &justread, NULL) && justread == sizeof(DWORD) && dwEndSig == MAPPING_END_SIGNATURE)
                  offset += sizeof(DWORD);
                  return true;
              }
            }
          }
        }
      }
    }
  }
  return false;
}

bool MappingFileClass::Parse(LPCTSTR szFolder) {
  if (FindCurrentMappingFile(szFolder)) {
    LARGE_INTEGER fileSize;
    if (GetFileSizeEx(m_hMappingHandle, &fileSize)) {
      if (fileSize.HighPart > 0)
        return false;
      LARGE_INTEGER zeroOffset;
      zeroOffset.QuadPart = 0;
      if (INVALID_SET_FILE_POINTER != SetFilePointer(m_hMappingHandle, zeroOffset.LowPart, &zeroOffset.HighPart, FILE_BEGIN)) {
        DWORD currentoffset = zeroOffset.LowPart;
        if (ParseMappingRecords(&m_aAlocatedDataPages, &m_aFreeDataPages, currentoffset, fileSize.LowPart))
          if (currentoffset < fileSize.LowPart) {
            zeroOffset.LowPart = currentoffset;
            if (INVALID_SET_FILE_POINTER != SetFilePointer(m_hMappingHandle, zeroOffset.LowPart, &zeroOffset.HighPart, FILE_BEGIN))
              return ParseMappingRecords(&m_aAlocatedIndexPages, &m_aFreeIndexPages, currentoffset, fileSize.LowPart);
          }
      }
    }
  }
  return false;
}

void MappingFileClass::PrintPages(std::vector<DWORD> *aPages) {
  if (!aPages)
    return;
  std::vector<DWORD>::iterator it = aPages->begin();
  int index = 0;
  wprintf(L"===============================================\n");
  wprintf(L"Logical Page | Physical Page\n");
  for (; it != aPages->end(); ++it) {
    wprintf(L"%.8X         | %.8X\n",index, *it);
    index++;
  }
  wprintf(L"===============================================\n");
}

void MappingFileClass::Print() {
  wprintf(L"Objects.data allocation map:\n");
  PrintPages(&m_aAlocatedDataPages);
  wprintf(L"Objects.data free map:\n");
  PrintPages(&m_aFreeDataPages);
  wprintf(L"===============================================\n");
  wprintf(L"Index.btr allocation map:\n");
  PrintPages(&m_aAlocatedIndexPages);
  wprintf(L"Index.btr free map:\n");
  PrintPages(&m_aFreeIndexPages);
}