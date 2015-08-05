#ifndef _DEFINED_MAPPING_H
#define _DEFINED_MAPPING_H

#include <vector>


#define MAX_MAPPING_FILES       0x3
#define MAPPING_START_SIGNATURE 0xABCD
#define MAPPING_END_SIGNATURE   0xDCBA
#define MAPPING_PAGE_ID_MASK    0x3FFFFFFF
#define MAPPING_PAGE_UNAVAIL    0xFFFFFFFF
#define MAPPING_FILE_CLEAN      0x1

class MappingFileClass {
public:

#pragma pack(4)
  struct MappingHeader {
    DWORD dwStartSignature;
    DWORD dwVersion;
    MappingHeader() : dwStartSignature(0), dwVersion() {}
    bool IsValid() const {
      return dwStartSignature == MAPPING_START_SIGNATURE && dwVersion;
    }
  };
  struct MappingXPHeader {
    MappingHeader sHeader;
    DWORD         dwPhysicalPages;
    DWORD         dwMappingEntries;
    bool IsValid() const {
      return sHeader.IsValid() && dwPhysicalPages && dwMappingEntries;
    }
  };

  struct MappingWin7Header {
    MappingHeader sHeader;
    DWORD dwFirstID;
    DWORD dwSecondID;
    DWORD dwPhysicalPages;
    DWORD dwMappingEntries;
    bool IsValid() const {
      return sHeader.IsValid() && dwPhysicalPages && dwMappingEntries;
    }

  };

  struct MappingOnDiskEntry {
    DWORD dwPageNumber;
    DWORD dwPageCRC;
    DWORD dwFreeSpace;
    DWORD dwUserData;
    DWORD dwFirstID;
    DWORD dwSecondID;
  };
#pragma pack()

  struct MappingEntry {
    DWORD dwPageNumber;
    DWORD dwPageCRC;
    DWORD dwFreeSpace;
    DWORD dwUserData;
    MappingEntry(DWORD dwpNum, DWORD dwCrc = 0, DWORD dwFreeSpace = 0, DWORD dwWrittenSpace = 0) : 
      dwPageNumber(dwpNum),
      dwPageCRC(dwCrc),
      dwFreeSpace(dwFreeSpace),
      dwUserData(dwWrittenSpace)
    {}
  };

  MappingFileClass();
  ~MappingFileClass();

  bool Parse(LPCTSTR szFolder);
  std::vector<DWORD>* GetIndexAllocMap() { return &m_aAlocatedIndexPages;}
  std::vector<DWORD>* GetIndexFreeMap() { return &m_aFreeIndexPages; }
  std::vector<DWORD>* GetDataAllocMap() { return &m_aAlocatedDataPages; }
  std::vector<DWORD>* GetDataFreeMap() { return &m_aFreeDataPages; }
  bool IsXPRepository() { return m_bXPRepository; }
  DWORD GetIndexRootPage() { return m_dwIndexRootPage; }
  void Print();

private:
  bool FindCurrentMappingFile(LPCTSTR szFolder);
  bool  ReadVersion(HANDLE hMappingFile, DWORD &version);
  bool  ParseMappingRecords(std::vector<DWORD> *aPhyDataPages, std::vector<DWORD> *aFreePages, DWORD& offset, DWORD filesize);
  void PrintPages(std::vector<DWORD> *aPages);


  HANDLE m_hMappingHandle;
  int    m_wszMappingIndex;
  bool   m_bCleanShutdown;
  bool   m_bXPRepository;
  DWORD  m_dwIndexRootPage;
  std::vector<DWORD> m_aAlocatedDataPages;
  std::vector<DWORD> m_aFreeDataPages;
  std::vector<DWORD> m_aAlocatedIndexPages;
  std::vector<DWORD> m_aFreeIndexPages;
};
#endif