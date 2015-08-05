#ifndef _DEFINED_INSTANCEDEC_H
#define _DEFINED_INSTANCEDEC_H

#include "Helper.h"
#include "Mapping.h"
#include "ClassDef.h"

class InstanceValue {
public:
  InstanceValue(StringValue &name, uint32 builtinID, uint32 type);
  ~InstanceValue();
  ExtentVectorVectorType& GetValue() { return Value; }
  bool SetDefaultValue(ExtentVectorVectorType& defVal);
  void Print(HANDLE hFile, FILE *out);

private:
  StringValue              NameValue;
  ExtentVectorVectorType   Value;
  uint32                   CimType;
  uint32                   BuiltInNameID;
};

class InstanceClass : public ObjectHeaderClass {
public:
  InstanceClass();
  virtual ~InstanceClass();
  std::vector<InstanceValue>& GetValues() { return Values; }
  virtual void Print(HANDLE hFile, FILE *out);

private:
  std::vector<InstanceValue> Values;
};

class InstanceDeclarationParser {
public:
  enum DefaultValInstanceConstFlags {
    PROP_IS_NOT_INITIALIZED = 1,
    PROP_USE_DEFAULT_VALUE  = 2
  };

#pragma pack(1)
  struct ClassNameStruct {
    uint32 ClassNameOffset;
    BYTE   Unk;

    bool IsValid() const {
      return !Unk && !ClassNameOffset;
    }
  };
#pragma pack()

  InstanceDeclarationParser(const wchar_t* path, const wchar_t* szNamespace, MappingFileClass &map);
  ~InstanceDeclarationParser();

  bool Parse(const wchar_t* szClass, const wchar_t* szInstanceName, const wchar_t *logpath);
  bool Parse(const wchar_t* szClass, const wchar_t *logpath);
  bool ParseInAllNS(const wchar_t* szClassName, const wchar_t *logpath);

private:
  static void BuildInstanceSearchString(std::wstring& szNamespace, const wchar_t* szClass, const wchar_t* szInstanceName, std::string& szSearch, bool bXP);
  static void BuildInstanceSearchString(std::wstring& szNamespace, const wchar_t* szClass, std::string& szSearch, bool bXP);
  static bool ParseClassRecordLocation(std::string &strIn, LocationStruct &ls);
  InstanceClass* ParseInstance(ClassDefinition& classDef, LocationStruct& ls);
  InstanceClass* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, ClassDefinition& classDef, bool bXP);
  bool Init();
  void Print(InstanceClass &inst, const wchar_t *logpath, const wchar_t *szNamespace, const wchar_t *szClassname);

  MappingFileClass            &Map;
  std::wstring                Namespace;
  std::wstring                Path;
  HANDLE                      m_ObjFile;
  bool                        m_bXP;

};
#endif