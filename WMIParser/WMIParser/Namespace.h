#ifndef _DEFINED_NAMESPACE_H
#define _DEFINED_NAMESPACE_H

#include "Mapping.h"

class WMINamespaceClass {
public:
  enum {
    NS_MAX_STRING_XP_SIZE     = 0x24,
    NS_MAX_STRING_XP_COUNT    = 0x20,
    NS_MAX_STRING_WIN7_SIZE   = 0x44,
    NS_MAX_STRING_WIN7_COUNT  = 0x40,
    NS_BYTES_BYPASS              = 0x06
  };

  struct NamespaceStruct {
    char  ParentNS[NS_MAX_STRING_WIN7_SIZE];
    char  InstanceNS[NS_MAX_STRING_WIN7_SIZE];
    DWORD LogicalID;
    DWORD RecordID;
    DWORD Size;
  };

  WMINamespaceClass(MappingFileClass &map);
  ~WMINamespaceClass();

  bool ParseNamespaceRecords(const wchar_t *path);
  void Close();
  std::vector<std::wstring>* GetNamespaces();
  void Print(const wchar_t *log);

private:
  bool                          m_bXP;
  HANDLE                        m_ObjFile;
  MappingFileClass              &Map;
  std::vector<std::wstring>     NamespaceNames;

  bool Init(const wchar_t *path);
  bool ParseNSRecord(WMINamespaceClass::NamespaceStruct &rec, std::wstring &ns);
  bool FindRecord(DWORD dwPhyPage, DWORD dwRecordID, DWORD dwSize, std::wstring &ns);
  bool ParseNSRecord(const BYTE *rec, DWORD dwSize, std::wstring &ns);
  bool AddNamespaceRecord(std::string &strIn, NamespaceStruct &ns);

  static void BuildSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
  static void BuildNSInstanceSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
};

#endif