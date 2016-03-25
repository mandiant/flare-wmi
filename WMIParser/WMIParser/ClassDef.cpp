#include "stdafx.h"
#include "ClassDef.h"
#include "indexBTR.h"
#include "Namespace.h"
#include <algorithm>

const QualifierClass::TypeSizes QualifierClass::CimTypeSizesArray[] = {
  VT_EMPTY, 0, true, L"CIM_EMPTY",
  VT_I2, sizeof(short), true, L"CIM_SINT16",
  VT_I4, sizeof(int), true, L"CIM_SINT32",
  VT_R4, sizeof(uint32), true, L"CIM_REAL32",
  VT_R8, sizeof(uint64), true, L"CIM_REAL64",
  VT_BSTR, sizeof(uint32), false, L"CIM_STRING",
  VT_BOOL, sizeof(uint16), true, L"CIM_BOOLEAN",
  VT_UNKNOWN, sizeof(uint32), false, L"CIM_OBJECT",
  VT_I1, sizeof(char), true, L"CIM_SINT8",
  VT_UI1, sizeof(BYTE), true, L"CIM_UINT8",
  VT_UI2, sizeof(uint16), true, L"CIM_UINT16",
  VT_UI4, sizeof(uint32), true, L"CIM_UINT32",
  VT_I8, sizeof(__int64), true, L"CIM_SINT64",
  VT_UI8, sizeof(uint64), true, L"CIM_UINT64",
  VT_DATETIME, sizeof(uint32), false, L"CIM_DATETIME",
  VT_REFERENCE, sizeof(uint32), false, L"CIM_REFERENCE",
  VT_CHAR16, sizeof(uint32), true, L"CIM_CHAR16",
  VT_ILLEGAL, 0, true, L"CIM_ILLEGAL"
};

const QualifierClass::BuiltInNames QualifierClass::BuiltInNamesArray[] = {
  QUALIFIER_PROP_PRIMARY_KEY,   L"PrimaryKey",
  QUALIFIER_PROP_READ,          L"Read",
  QUALIFIER_PROP_WRITE,         L"Write",
  QUALIFIER_PROP_VOLATILE,      L"Volatile",
  QUALIFIER_CLASS_PROVIDER,     L"Provider",
  QUALIFIER_CLASS_DYNAMIC,      L"Dynamic",
  QUALIFIER_PROP_TYPE,          L"Type"
};

QualifierClass::QualifierClass(uint32 offsetOrId, uint32 cimType) : Offset(offsetOrId), Type(cimType) {}

QualifierClass::~QualifierClass() {
}

void QualifierClass::SetName(std::vector<ExtentClass>& ex) {
  Name.Set(ex, TS_STRING);
}

const QualifierClass::TypeSizes* QualifierClass::GetTypeSizeStruct(int typeId) {
  typeId &= QUALIFIER_PROP_TYPE_ARRAY - 1;
  for (int i = 0; i < _countof(CimTypeSizesArray); ++i) {
    if (CimTypeSizesArray[i].CimType == typeId)
      return CimTypeSizesArray + i;
  }
  wprintf_s(L"QualifierClass::GetTypeSizeStruct(0x%X) -> failed.\r\n", typeId);
  return 0;
}

const QualifierClass::TypeSizes* QualifierClass::GetTypeSize(int typeId, bool& isarray) {
  isarray = (typeId & QUALIFIER_PROP_TYPE_ARRAY) > 0;
  typeId &= QUALIFIER_PROP_TYPE_ARRAY - 1;
  for (int i = 0; i < _countof(CimTypeSizesArray); ++i) {
    if (CimTypeSizesArray[i].CimType == typeId)
      return CimTypeSizesArray + i;
  }
  wprintf_s(L"QualifierClass::GetTypeSize(0x%X) -> failed.\r\n", typeId);
  return 0;
}

const wchar_t* QualifierClass::GetTypeName(int id) {
  id &= (QualifierClass::QUALIFIER_PROP_TYPE_ARRAY - 1);
  for (int i = 0; i < _countof(CimTypeSizesArray); ++i) {
    if (CimTypeSizesArray[i].CimType == id)
      return CimTypeSizesArray[i].Name;
  }
  wprintf_s(L"QualifierClass::GetTypeName(0x%X) -> failed.\r\n", id);
  return 0;
}

const wchar_t* QualifierClass::GetBuiltInName(int id) {
  //id &= (QualifierClass::QUALIFIER_PROP_TYPE_ARRAY - 1);
  id &= (QualifierClass::QUALIFIER_BUILTIN - 1);
  for (int i = 0; i < _countof(BuiltInNamesArray); ++i) {
    if (BuiltInNamesArray[i].CimId == id)
      return BuiltInNamesArray[i].Name;
  }
  wprintf_s(L"QualifierClass::GetBuiltInName(0x%X) -> failed.\r\n", id);
  return 0;
}

ClassDefinitionParser::ClassDefinitionParser(const wchar_t* path, MappingFileClass &map, const wchar_t* szNamespace) : Map(map), Path(path), Namespace(szNamespace), m_ObjFile(INVALID_HANDLE_VALUE), m_bXP(map.IsXPRepository()) {
}

ClassDefinitionParser::~ClassDefinitionParser(){
  if (m_ObjFile != INVALID_HANDLE_VALUE)
    ::CloseHandle(m_ObjFile);
}

bool ClassDefinitionParser::Init(const wchar_t *path) {
  HANDLE hFile = InitObjFile(path);
  if (hFile != INVALID_HANDLE_VALUE) {
    m_ObjFile = hFile;
    return true;
  }
  return false;
}

void ClassDefinitionParser::BuildClassSearchString(std::wstring& szNamespace, const wchar_t* szClass, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CD_<CLASSNAME>.recordID.locagicalOffset.size
  std::string strID;
  std::wstring name(szClass);
  GetStrId(strID, szNamespace, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_DEF_PREFIX;
  GetStrId(strID, name, bXP);
  szSearch += strID;
}

void ClassDefinitionParser::BuildClassSearchString(std::wstring& szNamespace, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CD_<CLASSNAME>.recordID.locagicalOffset.size
  std::string strID;
  GetStrId(strID, szNamespace, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_DEF_PREFIX;
}

bool ClassDefinitionParser::ParseClassRecordLocation(std::string &strIn, LocationStruct &ls) {
  bool ret = false;
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      int index = 0;
      while (index < 3) {
        char *szDot = strrchr(szIn, '.');
        if (!szDot)
          goto Exit;
        char *val = szDot + 1;
        *szDot = 0;
        if (!index)
          ls.Size = atoll(val) & ALL_BITS_32;
        else if (1 == index)
          ls.RecordID = atoll(val) & ALL_BITS_32;
        else
          ls.LogicalID = atoll(val) & ALL_BITS_32;
        index++;
      }
      ret = true;
    }
  Exit:
    delete[] szIn;
  }
  return ret;
}

bool ClassDefinitionParser::Print(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szClassName, MappingFileClass &map, const wchar_t *logpath) {
  ClassDefinition* pclassDef = 0;
  ClassDefinitionParser parser(path, map, szNamespace);
  if (parser.Parse(path, szClassName, map, &pclassDef) && pclassDef) {
    parser.Print(*pclassDef, szNamespace, logpath);
    delete pclassDef;
    return true;
  }
  return false;
}

bool ClassDefinitionParser::Print(const wchar_t* path, const wchar_t* szNamespace, MappingFileClass &map, const wchar_t *logpath) {
  std::vector<ClassDefinition*> classes;
  ClassDefinitionParser parser(path, map, szNamespace);
  if (parser.ParseAllInNS(path, map, classes)) {
    std::vector<ClassDefinition*>::iterator it = classes.begin();
    for (; it != classes.end(); ++it) {
      ClassDefinition *pclassDef = *it;
      parser.Print(*pclassDef, szNamespace, logpath);
      delete pclassDef;
    }
    return true;
  }
  return false;
}

bool ClassDefinitionParser::Print(const wchar_t* path, MappingFileClass &map, const wchar_t *logpath) {
  if (Print(path, L"__SystemClass", map, logpath)) {
    WMINamespaceClass ns(map);
    if (ns.ParseNamespaceRecords(path)) {
      ns.Close();
      std::vector<std::wstring> *nsNames = ns.GetNamespaces();
      if (nsNames && nsNames->size()) {
        std::vector<std::wstring>::iterator it = nsNames->begin();
        for (; it != nsNames->end(); ++it) {
          const wchar_t *ns = it->c_str();
          if (!Print(path, ns, map, logpath))
            wprintf_s(L"Failed to print \'%s\' namespace classes\r\n", ns);
        }
        return true;
      }
    }
  }
  else
    wprintf_s(L"Failed to print \'__SystemClass\' namespace classes\r\n");
  return false;
}

void ClassDefinitionParser::SetNamespace(const wchar_t* szNamespace) {
  Namespace = szNamespace;
}

bool ClassDefinitionParser::ParseAll(const wchar_t* path, MappingFileClass &map, std::vector<ClassDefinition*>& classes) {
  if (ParseAllInNS(path, map, classes)) {
    WMINamespaceClass ns(map);
    if (ns.ParseNamespaceRecords(path)) {
      ns.Close();
      std::vector<std::wstring> *nsNames = ns.GetNamespaces();
      if (nsNames) {
        std::vector<std::wstring>::iterator it = nsNames->begin();
        bool bError = false;
        for (; it != nsNames->end(); ++it) {
          const wchar_t *n = it->c_str();
          ClassDefinitionParser parser(path, map, n);
          if (!parser.ParseAllInNS(path, map, classes)) {
            wprintf_s(L"Failed to parse classes in namespace %s\r\n", n);
            bError = true;
            break;
          }
        }
        return !bError;
      }
    }
  }
  return false;
}

bool ClassDefinitionParser::ParseAllInNS(const wchar_t* path, MappingFileClass &map, std::vector<ClassDefinition*>& classes) {
  bool ret = false;
  if (!Namespace.empty()) {
    if (Init(path)) {
      std::string szSearch;
      LocationStruct ls;
      BuildClassSearchString(Namespace, szSearch, m_bXP);
      IndexBTR index(m_bXP);
      if (index.SearchBTRFile(path, Map, szSearch)) {
        std::vector<std::string> *records = index.GetResults();
        if (records) {
          if (!records->size()) {
            wprintf_s(L"No classes defined in %S namespace.\r\n", Namespace.c_str());
            return true;
          }
          std::vector<std::string>::iterator it = records->begin();
          for (; it != records->end(); ++it) {
            if (ParseClassRecordLocation(*it, ls)) {
              ClassDefinition *classDef = 0;
              bool bNonFatalError = false;
              if (CreateClassDefinition(bNonFatalError, ls, &classDef)) {
                if (classDef && !bNonFatalError)
                  classes.push_back(classDef);
                else
                  wprintf_s(L"Empty class def : %S\r\n", it->c_str());
              }
              else {
                wprintf_s(L"Failed to parse class def : %S\r\n",it->c_str());
                break;
              }
            }
          }
          ret = true;
        }
      }
    }
  }
  return ret;
}

bool ClassDefinitionParser::Parse(const wchar_t* path, const wchar_t* szClassName, MappingFileClass &map, ClassDefinition **ppclassDef) {
  return Init(path) && ParseClassDefinition(szClassName, ppclassDef);
}

bool ClassDefinitionParser::ParseClassDefinition(const wchar_t* szClassName, ClassDefinition **classDef) {
  bool ret = false;
  if (!Namespace.empty() && szClassName && classDef) {
    std::string szSearch;
    LocationStruct ls;
    BuildClassSearchString(Namespace, szClassName, szSearch, m_bXP);
    ret = FindDefinitionRecord(szSearch, ls);
    if (!ret) {
      std::wstring sysnamespace(L"__SystemClass");
      BuildClassSearchString(sysnamespace, szClassName, szSearch, m_bXP);
      ret = FindDefinitionRecord(szSearch, ls);
    }
    if (!ret)
      wprintf_s(L"No %s class defined in %s namespace.\r\n", szClassName, Namespace.c_str());
    bool bNonFatalError = false;
    ret = !ret || CreateClassDefinition(bNonFatalError, ls, classDef);
  }
  return ret;
}

bool ClassDefinitionParser::FindDefinitionRecord(std::string &path, LocationStruct& ls) {
  bool ret = false;
  IndexBTR index(m_bXP);
  if (index.SearchBTRFile(Path.c_str(), Map, path)) {
    std::vector<std::string> *records = index.GetResults();
    if (records && records->size()) {
      std::vector<std::string>::iterator it = records->begin();
      for (; it != records->end(); ++it) {
        ret = ParseClassRecordLocation(*it, ls);
        break;
      }
    }
  }
  return ret;
}

bool ClassDefinitionParser::CreateClassDefinition(bool& bNotFatalError, LocationStruct &ls, ClassDefinition **classDef) {
  bool ret = false;
  bNotFatalError = false;
  if (ls.IsValid()) {
    //wprintf_s(L"Class logical location: [%X.%X]\r\n", ls.LogicalID, ls.Size);
    std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
    if (allocMap) {
      std::vector<ExtentClass> recordExtents;
      if (!GetRecordExtents(m_ObjFile, *allocMap, ls, recordExtents)) {
        bNotFatalError = true;
        return true;
      }
      BYTE *recBuf = new BYTE[ls.Size];
      if (recBuf) {
        std::vector<ExtentClass>::iterator it = recordExtents.begin();
        DWORD currentIndex = 0;
        DWORD justread = 0;
        //wprintf_s(L"=========================Class physical location ====================\r\n");
        for (; it != recordExtents.end(); ++it) {
          LARGE_INTEGER offset;
          offset.QuadPart = it->GetStart();
          if (INVALID_SET_FILE_POINTER != SetFilePointer(m_ObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
            DWORD toRead = static_cast<DWORD>(it->GetCount() & ALL_BITS_32);
            //wprintf_s(L"Class physical location: [%X.%X]\r\n", offset.LowPart, toRead);
            if (::ReadFile(m_ObjFile, recBuf + currentIndex, toRead, &justread, NULL) && toRead == justread) {
              currentIndex += toRead;
            }
            else
              break;
          }
          else
            break;
        }
        //wprintf_s(L"======================================================================\r\n");
        ret = Create(recBuf, recordExtents, ls.Size, classDef);
        delete[] recBuf;
      }
    }
  }
  return ret;
}

void ClassDefinitionParser::Print(ClassDefinition &classDef, const wchar_t *szNamespace, const wchar_t *logpath) {
  FILE* pOutFile = CreateLogFile(logpath, L"at, ccs=UNICODE");
  MyPrintFunc(pOutFile, L"Namespace : %s\r\n", szNamespace);
  classDef.Print(m_ObjFile, pOutFile);
  if (pOutFile)
    ::fclose(pOutFile);
}

bool ClassDefinitionParser::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, ClassDefinition **ppclassDef) {
  if (recordBuf && cRecordExtents.size() && size && ppclassDef) {
    bool derived = false;
    if (!*ppclassDef)
      *ppclassDef = new ClassDefinition;
    else
      derived = true;
    ClassDefinition *pObject = *ppclassDef;
    if (pObject) {
      const BYTE* parseBuf = reinterpret_cast<const BYTE*>(recordBuf);
      uint32 currentOffset = 0;
      if (currentOffset + sizeof(uint32) < size) {
        uint32 superClassNameLen = *reinterpret_cast<const uint32*>(parseBuf);
        currentOffset += sizeof(uint32);
        if (superClassNameLen) {
          bool exit = false;
          if (currentOffset + superClassNameLen * sizeof(wchar_t) < size) {
            wchar_t *wszSuperClassName = new wchar_t[superClassNameLen + 1];
            if (wszSuperClassName) {
              if (!wcsncpy_s(wszSuperClassName, superClassNameLen + 1, reinterpret_cast<const wchar_t*>(parseBuf + currentOffset), superClassNameLen))
                exit = !ParseClassDefinition(wszSuperClassName, ppclassDef);
              else
                exit = true;
              delete[] wszSuperClassName;
            }
            else
              exit = true;
          }
          else
            exit = true;
          if (exit)
            return false;
          currentOffset += superClassNameLen * sizeof(wchar_t);
        }
        if (currentOffset + sizeof(uint64) < size) {
          if (!derived)
            pObject->SetDate(*reinterpret_cast<const uint64*>(parseBuf + currentOffset));
          currentOffset += sizeof(uint64);
        }
        else
          return false;
        uint32 propdatasize = 0;
        if (currentOffset + sizeof(uint32) < size) {
          propdatasize = *reinterpret_cast<const uint32*>(parseBuf + currentOffset);
          currentOffset += sizeof(uint32);
          if (currentOffset + propdatasize < size) {
            const ClassDefinition::JunkHeader *junkHeader = 0;
            if (currentOffset + sizeof(ClassDefinition::JunkHeader) < size) {
              const ClassDefinition::JunkHeader *junkHeader = reinterpret_cast<const ClassDefinition::JunkHeader *>(parseBuf + currentOffset);
              currentOffset += sizeof(ClassDefinition::JunkHeader);
              if (currentOffset + sizeof(uint32) < size) {
                uint32 superclassrecordsize = *reinterpret_cast<const uint32*>(parseBuf + currentOffset);
                if (currentOffset + superclassrecordsize < size) {
                  currentOffset += superclassrecordsize;
                  if (currentOffset + sizeof(uint32) < size) {
                    uint32 qualifiersize = *reinterpret_cast<const uint32*>(parseBuf + currentOffset);
                    if (currentOffset + qualifiersize < size) {
                      uint32 qualifiersOffset = currentOffset + sizeof(uint32);
                      const BYTE *classQualifiersMeta = reinterpret_cast<const BYTE*>(parseBuf + qualifiersOffset);
                      currentOffset += qualifiersize;
                      if (currentOffset + sizeof(uint32) < size) {
                        uint32 propcount = *reinterpret_cast<const uint32*>(parseBuf + currentOffset);
                        currentOffset += sizeof(uint32);
                        const BYTE *propMeta = reinterpret_cast<const BYTE*>(parseBuf + currentOffset);
                        if (currentOffset + propcount * sizeof(PropertyClass::PropMetaHeader) + junkHeader->DefaultValueSize + sizeof(uint32) < size) {
                          std::vector<ExtentClass> defaultValues;
                          uint32 defValueOffset = currentOffset + propcount * sizeof(PropertyClass::PropMetaHeader);
                          CreateFieldExtents(defValueOffset, junkHeader->DefaultValueSize, cRecordExtents, defaultValues);
                          uint32 dataSize = *reinterpret_cast<const uint32*>(parseBuf + currentOffset + propcount * sizeof(PropertyClass::PropMetaHeader) + junkHeader->DefaultValueSize) & 0x3FFFFFFF;
                          uint32 dataOffset = currentOffset + propcount * sizeof(PropertyClass::PropMetaHeader) + junkHeader->DefaultValueSize + sizeof(uint32);
                          if (dataOffset + dataSize < size) {
                            std::vector<ExtentClass> exNameValue;
                            uint32 inClassNameDatasize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(parseBuf + dataOffset + junkHeader->ClassNameDataOffset + sizeof(BYTE))));
                            CreateFieldExtents(dataOffset + junkHeader->ClassNameDataOffset + sizeof(BYTE), inClassNameDatasize, cRecordExtents, exNameValue);
                            if (derived)
                              pObject->AddBaseClass(exNameValue);
                            else
                              pObject->SetName(exNameValue);
                            return (derived || !qualifiersize || pObject->ParseClassQualifiers(parseBuf, cRecordExtents, qualifiersOffset, dataOffset, qualifiersize)) &&
                              (!propcount || pObject->ParseClassProperties(parseBuf, cRecordExtents, defaultValues, currentOffset, dataOffset, propcount, defValueOffset, junkHeader->DefaultValueSize));
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  return false;
}

void ClassDefinition::SetName(std::vector<ExtentClass>& ex) {
  ClassName.Set(ex, TS_STRING);
}

void ClassDefinition::AddBaseClass(std::vector<ExtentClass>& ex) {
  BaseClasses.push_back(StringValue(ex, TS_STRING));
}

void ClassDefinition::PrintJunk(HANDLE hFile, FILE* outFile) {
  MyPrintFunc(outFile, L"================================Junk=========================================\r\n");
  ByteArrayValue(DefaultValues).Print(hFile, outFile);
  MyPrintFunc(outFile, L"=============================================================================\r\n");
}

void ClassDefinition::Print(HANDLE hFile, FILE* outFile) {
  MyPrintFunc(outFile, L"===============================Class Definition==============================\r\n");
  MyPrintFunc(outFile, L"Name: ");
  ClassName.Print(hFile, outFile);
  MyPrintFunc(outFile, L"Base Classes:\r\n");
  std::vector<StringValue>::reverse_iterator it_base_class = BaseClasses.rbegin();
  for (; it_base_class != BaseClasses.rend(); ++it_base_class)
    it_base_class->Print(hFile, outFile);
  MyPrintFunc(outFile, L"Created: ");
  Date.Print(outFile);
  MyPrintFunc(outFile, L"Class Qualifiers:\r\n");
  std::vector<QualifierClass>::iterator it_qual = Qualifiers.begin();
  for (; it_qual != Qualifiers.end(); ++it_qual)
    it_qual->Print(hFile, outFile);
  MyPrintFunc(outFile, L"Class Properties:\r\n");
  std::vector<PropertyClass>::iterator it_prop = Properties.begin();
  for (; it_prop != Properties.end(); ++it_prop) {
    it_prop->Print(hFile, outFile);
  }
  MyPrintFunc(outFile, L"Class Size: 0x%X\r\n", GetSizeOfProps());
  //PrintJunk(hFile, outFile);
  MyPrintFunc(outFile, L"================================End of Class Definition=======================\r\n");
}

uint32 ClassDefinition::GetSizeOfProps() {
  uint32 classsize = 0;
  std::vector<PropertyClass>::iterator it_prop = Properties.begin();
  for (; it_prop != Properties.end(); ++it_prop) {
    uint32 cimType = it_prop->GetCimType();
    const QualifierClass::TypeSizes* p = QualifierClass::GetTypeSizeStruct(cimType);
    if (p) {
      if (cimType & QualifierClass::QUALIFIER_PROP_TYPE_ARRAY)
        classsize += sizeof(uint32);
      else
        classsize += p->CimOnDiskSize;
    }
  }
  return classsize;
}

ExtentVectorVectorType& QualifierClass::GetValueExtents() {
  return ValueExtents;
}

bool QualifierClass::ParseQualifiers(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, uint32 qualifiersOffset, uint32 dataOffset, uint32 qualifiersize, std::vector<QualifierClass> &qualifiers) {
  qualifiersize -= sizeof(uint32);
  uint32 inQualifiersOffset = 0;
  while (inQualifiersOffset + sizeof(QualifierHeader) < qualifiersize) {
    const QualifierHeader *header = reinterpret_cast<const QualifierHeader *>(record + qualifiersOffset + inQualifiersOffset);
    const QualifierClass::TypeSizes* qualSizeStruct = QualifierClass::GetTypeSizeStruct(header->QualifierType);
    if (qualSizeStruct) {
      QualifierClass qual(header->QualifierNameOffset, header->QualifierType);
      if (!header->IsBuiltInType()) {
        std::vector<ExtentClass> exName;
        uint32 inDataOffset = header->GetQualifierValue();
        uint32 inDatasize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(record + dataOffset + inDataOffset + sizeof(BYTE))));
        CreateFieldExtents(dataOffset + inDataOffset + sizeof(BYTE), inDatasize, cRecordExtents, exName);
        qual.SetName(exName);
      }
      ExtentVectorVectorType& qualExtents = qual.GetValueExtents();
      if (qualSizeStruct->Inline) {
        ExtentVectorType ext;
        CreateFieldExtents(qualifiersOffset + inQualifiersOffset + sizeof(QualifierHeader), qualSizeStruct->CimOnDiskSize, cRecordExtents, ext);
        qualExtents.push_back(ext);
      }
      else if (inQualifiersOffset + sizeof(QualifierHeader) + sizeof(uint32) <= qualifiersize) { //qualSizeStruct->CimOnDiskSize should be sizeof(uint32)
        uint32 inDataOffset = *reinterpret_cast<const uint32 *>(record + qualifiersOffset + inQualifiersOffset + sizeof(QualifierHeader));
        uint32 inDatasize = 0;
        if (header->QualifierType & QUALIFIER_PROP_TYPE_ARRAY) {
          SetMultiValueExtents(qualExtents, cRecordExtents, qualSizeStruct, record, dataOffset, inDataOffset);
        }
        else {
          ExtentVectorType ext;
          inDatasize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(record + dataOffset + inDataOffset + sizeof(BYTE))));
          CreateFieldExtents(dataOffset + inDataOffset + sizeof(BYTE), inDatasize, cRecordExtents, ext);
          qualExtents.push_back(ext);
        }
      }
      else {
        wprintf_s(L"Parse Qualifier Error : no room for qualifier value offset.\r\n");
        return false;
      }
      inQualifiersOffset += sizeof(QualifierHeader) + qualSizeStruct->CimOnDiskSize;
      qualifiers.push_back(qual);
    }
    else {
      wprintf_s(L"Parse Qualifier Error : Unknown Qualifier(0x%X)  Type = 0x%X\r\n", header->QualifierNameOffset, header->QualifierType);
      return false;
    }
  }
  return true;
}

void QualifierClass::Print(HANDLE hFile, FILE *outFile) {
  MyPrintFunc(outFile, L"===================================Qualifier=================================\r\n");
  bool builtin = (Offset & QualifierClass::QUALIFIER_BUILTIN) > 0;
  MyPrintFunc(outFile, L"Name: ");
  if (builtin) {
    const wchar_t* name = GetBuiltInName(Offset);
    if (name)
      MyPrintFunc(outFile, L"%s\r\n", name);
    else
      MyPrintFunc(outFile, L"Unknown Builtin Qualifier : 0x%x\r\n", Offset);
  }
  else
    Name.Print(hFile, outFile);
  bool isArray = (Type & QualifierClass::QUALIFIER_PROP_TYPE_ARRAY) > 0;
  MyPrintFunc(outFile, L"Type: ");
  const wchar_t* type_name = QualifierClass::GetTypeName(Type);
  if (type_name)
    MyPrintFunc(outFile, L"%s(0x%X)\r\n", type_name, Type);
  else
    MyPrintFunc(outFile, L"Unknown Qualifier Type : 0x%x\r\n", Type);
  MyPrintFunc(outFile, L"Array: %s\r\n", (isArray ? L"yes" : L"no"));
  MyPrintFunc(outFile, L"Value: ");

  uint32 t = Type & (QualifierClass::QUALIFIER_PROP_TYPE_ARRAY - 1);

  std::vector<ExtentVectorType>::iterator it_Value = ValueExtents.begin();
  for (; it_Value != ValueExtents.end(); ++it_Value) {
    if (t == VT_BSTR || t == VT_DATETIME || t == VT_REFERENCE)
      StringValue(*it_Value, TS_STRING).Print(hFile, outFile);
    else if (t == VT_UNKNOWN)
      ByteArrayValue(*it_Value).Print(hFile, outFile);
    else {
      uint32 size = 0;
      if (const void* val = GetBufferFromExtents(hFile, *it_Value, size)) {
        if ((t == VT_R4 || t == VT_I4 || t == VT_UI4) && size >= sizeof(uint32))
          MyPrintFunc(outFile, L"0x%.8X\r\n", *reinterpret_cast<const uint32*>(val));
        else if ((t == VT_I1 || t == VT_UI1) && size >= sizeof(BYTE))
          MyPrintFunc(outFile, L"0x%.2X\r\n", *reinterpret_cast<const BYTE*>(val));
        else if ((t == VT_I2 || t == VT_UI2) && size >= sizeof(uint16))
          MyPrintFunc(outFile, L"0x%.4X\r\n", *reinterpret_cast<const uint16*>(val));
        else if ((t == VT_R8 || t == VT_I8 || t == VT_UI8) && size >= sizeof(uint64))
          MyPrintFunc(outFile, L"0x%I64X\r\n", *reinterpret_cast<const uint64*>(val));
        else if (t == VT_BOOL && size >= sizeof(uint16)) {
          uint16 boolval = *reinterpret_cast<const uint16*>(val);
          MyPrintFunc(outFile, L"%s\r\n", (boolval == ALL_BITS_16) ? L"true" : L"false");
        }
        else
          ByteArrayValue(*it_Value).Print(hFile, outFile);
        delete[] val;
      }
    }
  }
  MyPrintFunc(outFile, L"===============================End of Qualifier==============================\r\n");
}

bool ClassDefinition::ParseClassQualifiers(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, uint32 currentOffset, uint32 dataOffset, uint32 qualifiersize) {
  return QualifierClass::ParseQualifiers(record, cRecordExtents, currentOffset, dataOffset, qualifiersize, Qualifiers);
}


PropertyClass::PropertyClass(uint32 type, uint32 offset, uint32 level, uint16 index) : CimType(type), OffsetInClass(offset), HierachyLevel(level), Index(index), NameOffset(0) {
}

void PropertyClass::SetNameOffset(uint32 nameOffset) {
  NameOffset = nameOffset;
}

void PropertyClass::Set(uint32 type, uint32 offset, uint32 level, uint16 index) {
  CimType = type;
  OffsetInClass = offset;
  HierachyLevel = level;
  Index = index;

}

void PropertyClass::SetName(std::vector<ExtentClass>& ex) {
  Name.Set(ex, TS_STRING);
}

std::vector<QualifierClass>& PropertyClass::GetQualifiers() {
  return Qualifiers;
}

bool operator<(const PropertyClass& cmp1, const PropertyClass& cmp2) {
  return (cmp1.Index < cmp2.Index);
}

uint16 PropertyClass::GetIndex() const {
  return Index;
}

bool PropertyClass::FindProp(uint16 index, std::vector<PropertyClass> &iprops) {
  std::vector<PropertyClass>::const_iterator it = iprops.cbegin();
  for (; it != iprops.cend(); ++it) {
    if (it->GetIndex() == index)
      return true;
  }
  return false;
}

void QualifierClass::SetMultiValueExtents(ExtentVectorVectorType &vec_Ext, std::vector<ExtentClass>& cRecordExtents, const QualifierClass::TypeSizes* types, const BYTE* recBuffer, uint32 dataOffset, uint32 inDataOffset) {
  std::vector<ExtentClass> ext;
  uint32 inDatasize = 0;
  if (types->CimType == VT_BSTR || types->CimType == QualifierClass::VT_DATETIME || types->CimType == QualifierClass::VT_REFERENCE) {
    const uint32 *offsets = reinterpret_cast<const uint32*>(recBuffer + dataOffset + inDataOffset);
    uint32 count = *offsets;
    while (count--) {
      ExtentVectorType ext;
      ++offsets;
      inDatasize = static_cast<uint32>(strlen(reinterpret_cast<const char*>(recBuffer + dataOffset + *offsets + sizeof(BYTE))));
      CreateFieldExtents(dataOffset + *offsets + sizeof(BYTE), inDatasize, cRecordExtents, ext);
      vec_Ext.push_back(ext);
    }
  }
  else if (types->CimType == VT_UNKNOWN) {
    inDatasize = *reinterpret_cast<const uint32*>(recBuffer + dataOffset + inDataOffset);
    CreateFieldExtents(dataOffset + inDataOffset + sizeof(uint32), inDatasize, cRecordExtents, ext);
    vec_Ext.push_back(ext);
  }
  else {
    inDatasize = *reinterpret_cast<const uint32*>(recBuffer + dataOffset + inDataOffset);
    uint32 chunks = inDatasize / types->CimOnDiskSize;
    uint32 currentdataoff = dataOffset + inDataOffset + sizeof(uint32);
    for (uint32 i = 0; i < chunks; ++i) {
      ExtentVectorType ext;
      CreateFieldExtents(currentdataoff + i*types->CimOnDiskSize, types->CimOnDiskSize, cRecordExtents, ext);
      vec_Ext.push_back(ext);
    }
  }
}

bool PropertyClass::ClearDefaultValue() {
  bool fail = false;
  try{
    std::vector<ExtentVectorType>::iterator it = DefaultValue.begin();
    for (; it != DefaultValue.end(); ++it)
      it->clear();
    DefaultValue.clear();
  }
  catch (...) {
    wprintf_s(L"ClearDefaultValue failed.\r\n");
    fail = true;
  }
  return !fail;
}

bool PropertyClass::SetDefaultValues(const BYTE* recBuffer, std::vector<PropertyClass> &props, std::vector<ExtentClass>& defaultValues, std::vector<ExtentClass>& cRecordExtents, uint32 dataOffset, uint32 defValOffset, uint32 defValSize) {
  uint32 propCount = static_cast<uint32>(props.size());
  if (propCount) {
    uint32 metaBytesCnt = propCount * 2;
    metaBytesCnt = metaBytesCnt / 8 + ((metaBytesCnt % 8) ? 1 : 0);
    const BYTE* metaBytes = recBuffer + defValOffset;
    const BYTE* defData = metaBytes + metaBytesCnt;
    const BYTE* enddefData = metaBytes + defValSize;
    if (defValSize > metaBytesCnt) {
      std::vector<PropertyClass>::iterator it = props.begin();
      uint32 idx = 0;
      for (; it != props.end(); ++it) {
        BYTE var = *(metaBytes + (idx / 4));
        BYTE flags = (var >> (2 * (idx % 4))) & 0x3;
        if (!(flags & DEFUALT_NO_VALUE) && !(flags & DEFAULT_INHERITED)) {
          PropertyClass &p = *it;
          p.ClearDefaultValue();
          ExtentVectorVectorType& vec_Ext = p.GetDefValue();
          uint32 inclassOff = p.GetOffsetInClass();
          bool isarray = false;
          const QualifierClass::TypeSizes* ptypes = QualifierClass::GetTypeSize(p.GetCimType(), isarray);
          if (ptypes) {
            uint32 vsize = ptypes->CimOnDiskSize;
            if (isarray)
              vsize = sizeof(uint32);
            if (defData + inclassOff + vsize <= enddefData) {
              std::vector<ExtentClass> ext;
              if (!isarray && ptypes->Inline) {
                CreateFieldExtents(defValOffset + metaBytesCnt + inclassOff, vsize, cRecordExtents, ext);
                vec_Ext.push_back(ext);
              }
              else {
                uint32 inDataOffset = *reinterpret_cast<const uint32*>(defData + inclassOff);
                if (isarray)
                  QualifierClass::SetMultiValueExtents(vec_Ext, cRecordExtents, ptypes, recBuffer, dataOffset, inDataOffset);
                else {
                  uint32 defLen = static_cast<uint32>(strlen(reinterpret_cast<const char*>(recBuffer + dataOffset + inDataOffset + sizeof(BYTE))));
                  CreateFieldExtents(dataOffset + inDataOffset + sizeof(BYTE), defLen, cRecordExtents, ext);
                  vec_Ext.push_back(ext);
                }
              }
            }
          }
        }
        idx++;
      }
      return true;
    }
  }
  return false;
}

bool PropertyClass::ParseProps(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, std::vector<ExtentClass>& defaultValues, uint32 propsOffset, uint32 dataOffset, uint32 propCount, uint32 defValOffset, uint32 defValSize, std::vector<PropertyClass> &iprops) {
  std::vector<PropertyClass> lprops;
  if (propCount) {
    const PropMetaHeader *propMetaCurrent = reinterpret_cast<const PropMetaHeader *>(record + propsOffset);
    const PropMetaHeader *propMetaEnd = propMetaCurrent + propCount;
    while (propMetaCurrent < propMetaEnd) {
      std::vector<ExtentClass> exName;
      const PropHeader* propHeader = reinterpret_cast<const PropHeader*>(record + dataOffset + propMetaCurrent->PropQualifiersOffset);
      PropertyClass prop(propHeader->PropType, propHeader->PropOffsetInClass, propHeader->PropClassLevel, propHeader->PropIndex);
      if (!propMetaCurrent->IsBuiltInType()) {
        uint32 propNameLen = static_cast<uint32>(strlen(reinterpret_cast<const char*>(record + dataOffset + propMetaCurrent->PropNameOffset + sizeof(BYTE))));
        CreateFieldExtents(dataOffset + propMetaCurrent->PropNameOffset + sizeof(BYTE), propNameLen, cRecordExtents, exName);
        prop.SetName(exName);
      }
      else
        prop.SetNameOffset(propMetaCurrent->PropNameOffset);
      if (QualifierClass::ParseQualifiers(record, cRecordExtents, dataOffset + propMetaCurrent->PropQualifiersOffset + sizeof(PropHeader), dataOffset, propHeader->PropQualifiersSize, prop.GetQualifiers())) {
        if (FindProp(propHeader->PropIndex, iprops)) {
          try {
            std::vector<ExtentVectorType>::iterator it = iprops[propHeader->PropIndex].GetDefValue().begin();
            for (; it != iprops[propHeader->PropIndex].GetDefValue().end(); ++it)
              prop.GetDefValue().push_back(*it);
            iprops[propHeader->PropIndex] = prop;
          }
          catch (...) {
            wprintf_s(L"PropertyClass::ParseProps - (Exisiting property) exception caught.\r\n");
          }
        }
        else
          iprops.push_back(prop);
      }
      else
        wprintf_s(L"Parse Props Qualifier Error.\r\n");
      propMetaCurrent++;
    }
    if (propMetaCurrent == propMetaEnd) {
      try {
        std::sort(iprops.begin(), iprops.end());
        return !defaultValues.size() || SetDefaultValues(record, iprops, defaultValues, cRecordExtents, dataOffset, defValOffset, defValSize);
      }
      catch (...) {
        wprintf_s(L"PropertyClass::ParseProps exception caught.\r\n");
      }
    }
    else
      wprintf_s(L"Not all the props have been parsed.\r\n");
  }
  return false;
}

void PropertyClass::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"====================================Property=================================\r\n");
  MyPrintFunc(out, L"Name: ");
  bool builtin = (NameOffset & QualifierClass::QUALIFIER_BUILTIN) > 0;
  if (builtin) {
    const wchar_t* name = QualifierClass::GetBuiltInName(NameOffset);
    if (name)
      MyPrintFunc(out, L"%s\r\n", name);
    else
      MyPrintFunc(out, L"Unknown Builtin Qualifier : 0x%x\r\n", NameOffset);
  }
  else
    Name.Print(hFile, out);
  MyPrintFunc(out, L"Type: ");
  MyPrintFunc(out, L"%s(0x%X)\r\n", QualifierClass::GetTypeName(CimType), CimType);
  bool isArray = (CimType & QualifierClass::QUALIFIER_PROP_TYPE_ARRAY) > 0;
  MyPrintFunc(out, L"Array: %s\r\n", (isArray ? L"yes" : L"no"));
  MyPrintFunc(out, L"Index: ");
  MyPrintFunc(out, L"0x%X\r\n", Index);
  MyPrintFunc(out, L"Offset: ");
  MyPrintFunc(out, L"0x%X\r\n", OffsetInClass);
  MyPrintFunc(out, L"Level: ");
  MyPrintFunc(out, L"0x%X\r\n", HierachyLevel);
  if (DefaultValue.size()) {
    MyPrintFunc(out, L"Default Value: ");
    uint32 t = CimType & (QualifierClass::QUALIFIER_PROP_TYPE_ARRAY - 1);
    std::vector<ExtentVectorType>::iterator it_def_val = DefaultValue.begin();
    for (; it_def_val != DefaultValue.end(); ++it_def_val) {
      if (t == VT_BSTR || t == QualifierClass::VT_DATETIME || t == QualifierClass::VT_REFERENCE)
        StringValue(*it_def_val, TS_STRING).Print(hFile, out);
      else if (t == VT_UNKNOWN)
        ByteArrayValue(*it_def_val).Print(hFile, out);
      else {
        uint32 size = 0;
        if (const void* val = GetBufferFromExtents(hFile, *it_def_val, size)) {
          if ((t == VT_R4 || t == VT_I4 || t == VT_UI4) && size >= sizeof(uint32))
            MyPrintFunc(out, L"0x%.8X", *reinterpret_cast<const uint32*>(val));
          else if ((t == VT_I1 || t == VT_UI1) && size >= sizeof(BYTE))
            MyPrintFunc(out, L"0x%.2X", *reinterpret_cast<const BYTE*>(val));
          else if ((t == VT_I2 || t == VT_UI2) && size >= sizeof(uint16))
            MyPrintFunc(out, L"0x%.4X", *reinterpret_cast<const uint16*>(val));
          else if ((t == VT_R8 || t == VT_I8 || t == VT_UI8) && size >= sizeof(uint64))
            MyPrintFunc(out, L"0x%I64X", *reinterpret_cast<const uint64*>(val));
          else if (t == VT_BOOL && size >= sizeof(uint16)) {
            uint16 boolval = *reinterpret_cast<const uint16*>(val);
            MyPrintFunc(out, L"%s", (boolval == ALL_BITS_16) ? L"true" : L"false");
          }
          else
            ByteArrayValue(*it_def_val).Print(hFile, out);
          delete [] val;
        }
      }
      if ((it_def_val + 1) != DefaultValue.end())
        MyPrintFunc(out, L", ");
    }
    MyPrintFunc(out, L"\r\n");
  }
  MyPrintFunc(out, L"Property Qualifiers:\r\n");
  std::vector<QualifierClass>::iterator it_qual = Qualifiers.begin();
  for (; it_qual != Qualifiers.end(); ++it_qual)
    it_qual->Print(hFile, out);
  MyPrintFunc(out, L"=================================End of Property=============================\r\n");
}

bool ClassDefinition::ParseClassProperties(const BYTE* record, std::vector<ExtentClass>& cRecordExtents, std::vector<ExtentClass>& defaultValues, uint32 propsOffset, uint32 dataOffset, uint32 propCount, uint32 defValOffset, uint32 defValSize) {
  return PropertyClass::ParseProps(record, cRecordExtents, defaultValues, propsOffset, dataOffset, propCount, defValOffset, defValSize, Properties);
}

void ClassDefinition::SetDate(uint64 date) {
  Date = date;
}
