#ifndef _DEFINED_CLASSDEF_H
#define _DEFINED_CLASSDEF_H

#include "Helper.h"
#include "Mapping.h"

class QualifierClass {
public:
  enum {
    VT_DATETIME  = 0x65,
    VT_REFERENCE = 0x66,
    VT_CHAR16    = 0x67,
    VT_ILLEGAL   = 0xFFF
  };

  enum BuiltInIds {
    QUALIFIER_PROP_PRIMARY_KEY = 0x1,
    QUALIFIER_PROP_READ        = 0x3,
    QUALIFIER_PROP_WRITE       = 0x4,
    QUALIFIER_PROP_VOLATILE    = 0x5,
    QUALIFIER_CLASS_PROVIDER   = 0x6,
    QUALIFIER_CLASS_DYNAMIC    = 0x7,
    QUALIFIER_PROP_TYPE        = 0xA
  };

  struct TypeSizes {
    uint32   CimType;
    uint32   CimOnDiskSize;
    bool     Inline;
    wchar_t  Name[0x10];
  };

  struct BuiltInNames {
    uint32   CimId;
    wchar_t  Name[0x10];
  };

#pragma pack(1)
  struct QualifierHeader {
    uint32 QualifierNameOffset;
    BYTE   Unk;
    uint32 QualifierType;

    bool IsBuiltInType() const {
      return (QualifierNameOffset & QualifierClass::QUALIFIER_BUILTIN) > 0;
    }

    bool IsArrayType() const {
      return (QualifierType & QualifierClass::QUALIFIER_PROP_TYPE_ARRAY) > 0;
    }

    uint32 GetQualifierValue() const {
      return QualifierNameOffset & (QualifierClass::QUALIFIER_BUILTIN - 1);
    }
  };
#pragma pack()

  QualifierClass(uint32 offsetOrId, uint32 cimType);
  ~QualifierClass();
  ExtentVectorVectorType& GetValueExtents();
  void SetName(std::vector<ExtentClass>& ex);

  void Print(HANDLE hFile, FILE *out);

  static const uint32 QUALIFIER_BUILTIN         = 0x80000000;
  static const uint32 QUALIFIER_PROP_TYPE_ARRAY = 0x00002000;
  static const uint32 QUALIFIER_PROP_TYPE_BYREF = 0x00004000;
  static const TypeSizes CimTypeSizesArray[];
  static const BuiltInNames BuiltInNamesArray[];

  static const TypeSizes* GetTypeSizeStruct(int typeId);
  static const wchar_t* GetBuiltInName(int id);
  static const wchar_t* GetTypeName(int id);
  static const TypeSizes* GetTypeSize(int typeId, bool& array);
  static bool ParseQualifiers(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, uint32 currentOffset, uint32 dataOffset, uint32 qualifiersize, std::vector<QualifierClass> &qualifiers);
  static void SetMultiValueExtents(ExtentVectorVectorType &vec_Ext, std::vector<ExtentClass>& cRecordExtents, const QualifierClass::TypeSizes* types, const BYTE* recBuffer, uint32 dataOffset, uint32 inDataOffset);

private:
  uint32                   Offset;
  uint32                   Type;
  StringValue              Name;
  ExtentVectorVectorType   ValueExtents;
};


class PropertyClass {
public:
  enum DefaultValConstFlags {
    DEFUALT_NO_VALUE  = 1,
    DEFAULT_INHERITED = 2
  };

#pragma pack(2)
  struct PropMetaHeader {
    uint32 PropNameOffset;
    uint32 PropQualifiersOffset;

    bool IsBuiltInType() const {
      return (PropNameOffset & QualifierClass::QUALIFIER_BUILTIN) > 0;
    }
  };

  struct PropHeader {
    uint32 PropType;
    uint16 PropIndex;
    uint32 PropOffsetInClass;
    uint32 PropClassLevel;
    uint32 PropQualifiersSize;
  };
#pragma pack()

  PropertyClass(uint32 type = 0, uint32 offset = 0, uint32 level = 0, uint16 index = 0);
  friend bool operator<(const PropertyClass& cmp1, const PropertyClass& cmp2);
  void SetName(std::vector<ExtentClass>& ex);
  std::vector<QualifierClass>& GetQualifiers();
  void Set(uint32 type, uint32 offset, uint32 level, uint16 index);
  void SetNameOffset(uint32 nameOffset);
  void Print(HANDLE hFile, FILE *out);
  uint16 GetIndex() const;
  static bool ParseProps(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, std::vector<ExtentClass>& defaultValues, uint32 propsOffset, uint32 dataOffset, uint32 propCount, uint32 defValOffset, uint32 defValSize, std::vector<PropertyClass> &props);
  static bool FindProp(uint16 index, std::vector<PropertyClass> &iprops);
  static bool SetDefaultValues(const BYTE* defValBuffer, std::vector<PropertyClass> &props, std::vector<ExtentClass>& defaultValues, std::vector<ExtentClass>& cRecordExtents, uint32 dataOffset, uint32 defValOffset, uint32 defValSize);
  uint32 GetCimType() { return CimType; }
  uint32 GetOffsetInClass() { return OffsetInClass; }
  bool ClearDefaultValue();
  ExtentVectorVectorType& GetDefValue() { return DefaultValue; }
  uint32 GetNameOffset() { return NameOffset; }
  StringValue& GetName() { return Name; }

private:
  std::vector<QualifierClass> Qualifiers;
  ExtentVectorVectorType      DefaultValue;
  StringValue                 Name;
  uint32                      NameOffset;
  uint32                      CimType;
  uint32                      OffsetInClass;
  uint32                      HierachyLevel;
  uint16                      Index;
  
};

class ClassDefinition {
public:
  ClassDefinition() {}
  
  void SetDate(uint64 date);

  bool ParseClassQualifiers(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, uint32 currentOffset, uint32 dataOffset, uint32 qualifiersize);
  bool ParseClassProperties(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, std::vector<ExtentClass>& defaultValues, uint32 propsOffset, uint32 dataOffset, uint32 propCount, uint32 defValOffset, uint32 defValSize);
  void Print(HANDLE objFile, FILE *pOutFile = 0);
  void PrintMeta(HANDLE objFile, FILE *pOutFile = 0);
  void SetName(std::vector<ExtentClass>& ex);
  void AddBaseClass(std::vector<ExtentClass>& ex);
  std::vector<ExtentClass>& GetDefaultValues() { return DefaultValues; }
  std::vector<PropertyClass>& GetProps() { return Properties; }
  void PrintJunk(HANDLE hFile, FILE* outFile);
  uint32 GetSizeOfProps();

#pragma pack(1)
  struct JunkHeader{
    BYTE   Unk;
    uint32 ClassNameDataOffset;
    uint32 DefaultValueSize;
  };

#pragma pack()


private:
  DateValue                   Date;
  StringValue                 ClassName;
  std::vector<StringValue>    BaseClasses;
  std::vector<QualifierClass> Qualifiers;
  std::vector<PropertyClass>  Properties;
  std::vector<ExtentClass>    DefaultValues;

  void ClassDefinition::PrintMetaHelper(HANDLE hFile, FILE* outFile);
};

class ClassDefinitionParser {
public:
  ClassDefinitionParser(const wchar_t* path, MappingFileClass &map, const wchar_t* szNamespace = L"__SytemClass");
  ~ClassDefinitionParser();
  static bool PrintMeta(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szClassName, MappingFileClass &map, const wchar_t *logpath);
  static bool Print(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szClassName, MappingFileClass &map, const wchar_t *logpath);
  static bool Print(const wchar_t* path, const wchar_t* szNamespace, MappingFileClass &map, const wchar_t *logpath);
  static bool Print(const wchar_t* path, MappingFileClass &map, const wchar_t *logpath);
  static bool PrintAllClasses(const wchar_t* path, const wchar_t* szClassName, MappingFileClass &map, const wchar_t *logpath);
  bool Parse(const wchar_t* path, const wchar_t* szClassName, MappingFileClass &map, std::vector<ClassDefinition*>& classes);
  bool Parse(const wchar_t* path, const wchar_t* szClassName, MappingFileClass &map, ClassDefinition **ppclassDef);
  bool ParseAllInNS(const wchar_t* path, MappingFileClass &map, std::vector<ClassDefinition*>& classes);
  bool ParseAll(const wchar_t* path, MappingFileClass &map, std::vector<ClassDefinition*>& classes);
  bool ParseClassDefinition(const wchar_t* szClassName, ClassDefinition **classDef);
  bool FindDefinitionRecord(std::string &path, LocationStruct& ls);
  bool FindRecords(std::wstring& ns, const wchar_t* szClassName, std::vector<LocationStruct> &lsrec);
  void Print(ClassDefinition &classDef, const wchar_t *szNamespace, const wchar_t *logpath);
  void PrintMeta(ClassDefinition &classDef, const wchar_t *szNamespace, const wchar_t *logpath);
  void SetNamespace(const wchar_t* szNamespace);

private:
  MappingFileClass            &Map;
  std::wstring                Namespace;
  std::wstring                Path;
  HANDLE                      m_ObjFile;
  bool                        m_bXP;

  bool Init(const wchar_t *path);
  bool CreateClassDefinition(bool& bFatal, LocationStruct &ls, ClassDefinition **classDef);
  bool Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, ClassDefinition **ppclassDef);
  static bool ParseClassRecordLocation(std::string &strIn, LocationStruct &ls);
  static void BuildClassSearchString(std::wstring& szNamespace, const wchar_t* szclass, std::string& szSearch, bool bXP);
  static void BuildClassSearchString(std::wstring& szNamespace, std::string& szSearch, bool bXP);
};
#endif