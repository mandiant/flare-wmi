#ifndef _DEFINED_EVENTFILTER_H
#define _DEFINED_EVENTFILTER_H

#include "Helper.h"
#include "Mapping.h"

class EventFilterParserClass {
public:
  EventFilterParserClass(MappingFileClass &map);
  ~EventFilterParserClass();
  bool ParseAllFilterInstances(const wchar_t* path, const wchar_t* szNamespace);
  bool ParseFilterInstance(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szInstance);
  void Print(const wchar_t *outlog, const wchar_t* szNamespace, const wchar_t* szInstance = 0);

private:
  std::vector<InstanceStruct>   Filters;
  MappingFileClass              &Map;
  HANDLE                        m_ObjFile;
  bool                          m_bXP;

  bool Init(const wchar_t *path);
  void BuildFilterClassSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
  void BuildFilterInstanceSearchString(const wchar_t* szNamespace, const wchar_t* szInst, std::string& szSearch, bool bXP);
  void BuildAllFilterInstancesSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
  bool GetNewFilterClass(std::string& strIn, const wchar_t* szNamespace, std::string& szFilterClass, bool bXP);
  void AddFilter(InstanceStruct& fs);
};

class EventFilterClass : public ObjectHeaderClass {
public:
  EventFilterClass();
  EventFilterClass(const EventFilterClass& copyin);

  virtual ~EventFilterClass();
  virtual void Print(HANDLE hFile, FILE *out);

  static EventFilterClass* Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, InstanceStruct &fs, bool bXP);

  static const wchar_t FILTER_NAME[];
  static const uint32 EFDataTypesSize = 6;
  static const ConsumerDataType EFDataTypes[EFDataTypesSize];
  static const uint32 UNK_7_BYTES = 7;

private:
  StringValue     Name;
  ByteArrayValue  CreatorSID;
  StringValue     QueryLanguage;
  StringValue     Query;
  StringValue     EventNamespace;
  Uint32Value     EventAccess;

  void SetCreatorSID(uint64 s, uint64 c);
  void SetCreatorSID(std::vector<ExtentClass>& extents);
  void SetName(uint64 s, uint64 c, int type);
  void SetName(std::vector<ExtentClass>& extents, int type);
  void SetQueryLanguage(uint64 s, uint64 c, int type);
  void SetQueryLanguage(std::vector<ExtentClass>& extents, int type);
  void SetQuery(uint64 s, uint64 c, int type);
  void SetQuery(std::vector<ExtentClass>& extents, int type);
  void SetEventNamespace(uint64 s, uint64 c, int type);
  void SetEventNamespace(std::vector<ExtentClass>& extents, int type);
  void SetEventAccess(uint32 val);
  static EventFilterClass* Create(HANDLE hObjFile, std::vector<ExtentClass>& cRecordExtents, DWORD cSize, bool bXP);
  static EventFilterClass* Create(std::vector<ExtentClass>& cRecordExtents, const void* recordBuf, uint32 size, bool bXP);
};
#endif