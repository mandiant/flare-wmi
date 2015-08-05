#ifndef _DEFINED_INDEXBTR_H
#define _DEFINED_INDEXBTR_H

#include "Mapping.h"

class IndexBTR {
public:
  typedef bool(*PCRITERIAFUNC) (std::string&, std::string&, bool);
  enum {
    NAMESPACE_INDEX         = 0x02
  };
#pragma pack(4)
  struct PageHeader {
    enum {
      PAGE_TYPE_UNK        = 0x0000,
      PAGE_TYPE_ACTIVE     = 0xACCC,
      PAGE_TYPE_DELETED    = 0xBADD,
      PAGE_TYPE_ADMIN      = 0xADDD
    };

    uint32 Sig;
    uint32 LogicalId;
    uint32 Zero1;
    uint32 XPRootPage;
    uint32 RecordCount;
    
    bool IsValid(uint32 index) const {
      return Sig == PAGE_TYPE_ACTIVE && index == LogicalId && RecordCount;
    }

    bool IsAdmin() const {
      return Sig == PAGE_TYPE_ADMIN;
    }

    bool IsDeleted() const {
      return Sig == PAGE_TYPE_DELETED;
    }

  };
#pragma pack()

  IndexBTR(bool bXP);
  ~IndexBTR();

  bool SearchBTRFile(const wchar_t* path, MappingFileClass &map, std::vector<std::string> &aSearch, FILE *out = 0);
  bool SearchBTRFile(const wchar_t* path, MappingFileClass &map, std::string &strSearch);
  std::vector<std::string> *GetResults() { return &m_aResult; };
  void ResetResults() { m_aResult.clear();}
  void Print(const wchar_t *logpath);

private:
  HANDLE                                          m_HFile;
  bool                                            m_bXP;
  std::vector<std::string>                        m_aResult;

  bool SearchBTRFile(DWORD index, std::vector<DWORD> *alocMap, std::vector<std::string> &aSearch, FILE *out);
  bool SearchBTRFile(DWORD index, std::vector<DWORD> *alocMap, std::string &strSearch);
  bool IsNamespaceInstance(const char* szIn);
  bool AddNamespaceRecord(char *szIn);
  DWORD GetRootPage(MappingFileClass &map);

  static bool NoCriteria(std::string& szIn, std::string& szSearch, bool bXP);
};
#endif