#ifndef _DEFINED_FILTERTOCONSUMERBINDING_H
#define _DEFINED_FILTERTOCONSUMERBINDING_H

#include "Helper.h"
#include "Mapping.h"

class FilterToConsumerBindingClass : public ObjectHeaderClass {
public:
  FilterToConsumerBindingClass();
  FilterToConsumerBindingClass(const FilterToConsumerBindingClass &copyin);
  
  virtual ~FilterToConsumerBindingClass();
  virtual void Print(HANDLE hFile, FILE *out);

  static FilterToConsumerBindingClass* Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, InstanceStruct &fs, bool bXP);

  static const wchar_t FILTER_TO_CONSUMER_BINDING_NAME[];
  static const uint32 FTCBDataTypesSize = 7;
  static const ConsumerDataType FTCBDataTypes[FTCBDataTypesSize];
  static const uint32 UNK_7_BYTES = 7;

private:
  StringValue     Filter;
  StringValue     Consumer;
  ByteArrayValue  CreatorSID;
  Uint32Value     DeliveryQoS;
  BoolValue       DeliverSynchronously;
  BoolValue       MaintainSecurityContext;
  BoolValue       SlowDownProviders;

  void SetCreatorSID(uint64 s, uint64 c);
  void SetCreatorSID(std::vector<ExtentClass>& extents);
  void SetConsumer(uint64 s, uint64 c, int type);
  void SetConsumer(std::vector<ExtentClass>& extents, int type);
  void SetFilter(uint64 s, uint64 c, int type);
  void SetFilter(std::vector<ExtentClass>& extents, int type);
  void SetDeliveryQoS(uint32 val);
  void SetDeliverSynchronously(uint16 val);
  void SetMaintainSecurityContext(uint16 val);
  void SetSlowDownProviders(uint16 val);

  static FilterToConsumerBindingClass* Create(HANDLE hObjFile, std::vector<ExtentClass>& cRecordExtents, DWORD cSize, bool bXP);
  static FilterToConsumerBindingClass* Create(std::vector<ExtentClass>& cRecordExtents, const void* recordBuf, uint32 size, bool bXP);
};

class FilterToConsumerBindingParserClass {
public:
  FilterToConsumerBindingParserClass(MappingFileClass &map);
  ~FilterToConsumerBindingParserClass();

  bool ParseAllBindings(const wchar_t* path, const wchar_t* szNamespace);
  void Print(const wchar_t* szNamespace, const wchar_t *outlog);

private:
  std::vector<InstanceStruct>  Bindings;
  MappingFileClass            &Map;
  HANDLE                      m_ObjFile;
  bool                        m_bXP;

  bool Init(const wchar_t *path);
  void BuildBindingInstanceSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
  void BuildBindingClassSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
  void AddBinding(InstanceStruct& fs);
  bool ConstructBindingRecord(std::string &strIn, InstanceStruct &fs);
  bool GetNewBindingClass(std::string& strIn, const wchar_t* szNamespace, std::string& szFilterClass, bool bXP);
};
#endif