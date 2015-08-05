#ifndef _DEFINED_CONSUMER_PARSER_H
#define _DEFINED_CONSUMER_PARSER_H

#include "Mapping.h"
#include "Helper.h"

class ConsumerParserClass {
public:
  struct BindingStruct {
    char           InstanceID[MAX_STRING_WIN7_SIZE];
    InstanceStruct Binding;

    bool IsValid() const {
      return Binding.IsValid();
    }
  };

  ConsumerParserClass(MappingFileClass &map);
  ~ConsumerParserClass();

  bool ParseAllConsumers(const wchar_t* path, const wchar_t* szNamespace);
  bool ParseAllConsumersByType(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* type);
  bool ParseConsumerInstance(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstanceName);
  
  void Print(const wchar_t* outlog, const wchar_t* szNamespace, const wchar_t* szType = 0);
  void Print(const wchar_t* outlog, const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance);

private:
  std::vector<InstanceStruct> Consumers;
  MappingFileClass            &Map;
  HANDLE                      m_ObjFile;
  bool                        m_bXP;
  
  bool Init(const wchar_t *path);
  bool ConstructConsumerRecord(std::string &strIn, const wchar_t* szNamespace, const wchar_t* szType, InstanceStruct& ns);
  bool ParseBinding(BindingStruct &binding, std::string &strIn, std::string &str);
  void AddConsumer(InstanceStruct& cs);
  InstanceStruct* FindConsumer(std::string &str, const wchar_t* szNamespace, const wchar_t* szType);

  static bool GetNewConsumerClass(std::string& szPath, const wchar_t* szNamespace, std::string& szConsumerClass, bool bXP);

  static void BuildInstanceSearchStringHelper(const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance, std::string& szSearch, bool bXP);

  static void BuildConsumerClassSearchString(const wchar_t* szNamespace, std::string& szSearch, bool bXP);
  static void BuildConsumerClassDefSearchString(const wchar_t* szNamespace, std::string& szClass, std::string& szSearch, bool bXP);

  static void BuildAllInstancesSearchString(const wchar_t* szNamespace, std::string& szClass, std::string& szSearch, bool bXP);
  static void BuildAllInstancesSearchString(const wchar_t* szNamespace, const wchar_t* szType, std::string& szSearch, bool bXP);

  static void BuildAllInstanceRefSearchString(const wchar_t* szNamespace, const wchar_t* szClass, std::string& szSearch, bool bXP);

  static void BuildInstanceSearchString(const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance, std::string& szSearch, bool bXP);

  static void BuildInstanceRefSearchString(const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance, std::string& szSearch, bool bXP);
  static void BuildInstanceRefSearchString(const wchar_t* szNamespace, const wchar_t* szType, std::string&  szInstance, std::string& szSearch, bool bXP);

  bool GetConsumerBinding(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType, std::vector<DWORD>& allocMap, InstanceStruct& cs, std::vector<InstanceStruct> &bindings);
};
#endif