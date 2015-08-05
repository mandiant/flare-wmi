#include "stdafx.h"
#include "InstanceDec.h"
#include "indexBTR.h"
#include "Namespace.h"
#include <iterator>

InstanceDeclarationParser::InstanceDeclarationParser(const wchar_t* path, const wchar_t* szNamespace, MappingFileClass &map) : 
  Path(path), 
  Namespace(szNamespace), 
  Map(map), 
  m_ObjFile(INVALID_HANDLE_VALUE), 
  m_bXP(map.IsXPRepository()) 
{
}

InstanceDeclarationParser::~InstanceDeclarationParser() {
  if (m_ObjFile != INVALID_HANDLE_VALUE) {
    ::CloseHandle(m_ObjFile);
    m_ObjFile = INVALID_HANDLE_VALUE;
  }
}

void InstanceDeclarationParser::BuildInstanceSearchString(std::wstring& szNamespace, const wchar_t* szClass, const wchar_t* szInstanceName, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CLASSNAME>\\IL_<INSTANCENAME>*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = szClass;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
  name = szInstanceName;
  GetStrId(strID, name, bXP);
  szSearch += strID;
}

void InstanceDeclarationParser::BuildInstanceSearchString(std::wstring& szNamespace, const wchar_t* szClass, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CLASSNAME>\\IL_*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = szClass;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
}

bool InstanceDeclarationParser::Init() {
  if (m_ObjFile != INVALID_HANDLE_VALUE)
    return true;
  if (Path.size()) {
    HANDLE hFile = InitObjFile(Path.c_str());
    if (hFile != INVALID_HANDLE_VALUE) {
      m_ObjFile = hFile;
      return true;
    }
  }
  return false;
}

bool InstanceDeclarationParser::ParseClassRecordLocation(std::string &strIn, LocationStruct &ls) {
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

bool InstanceDeclarationParser::ParseInAllNS(const wchar_t* szClassName, const wchar_t *logpath) {
  WMINamespaceClass ns(Map);
  if (ns.ParseNamespaceRecords(Path.c_str())) {
    ns.Close();
    std::vector<std::wstring> *nsNames = ns.GetNamespaces();
    if (nsNames) {
      std::vector<std::wstring>::iterator it = nsNames->begin();
      bool bError = false;
      for (; it != nsNames->end(); ++it) {
        Namespace = *it;
        if (!Parse(szClassName, logpath)) {
          wprintf_s(L"InstanceDeclarationParser::ParseInAllNS (%s\\%s) failed.\r\n", Namespace.c_str(), szClassName);
          bError = true;
          break;
        }
      }
      return !bError;
    }
  }
  return false;
}

bool InstanceDeclarationParser::Parse(const wchar_t* szClassName, const wchar_t* szInstanceName, const wchar_t *logpath) {
  bool ret = false;
  if (Init()) {
    ClassDefinition *pclassDef = 0;
    ClassDefinitionParser classParser(Path.c_str(), Map, Namespace.c_str());
    if (classParser.Parse(Path.c_str(), szClassName, Map, &pclassDef)) {
      if (pclassDef) {
        std::string szSearch;
        BuildInstanceSearchString(Namespace, szClassName, szInstanceName, szSearch, m_bXP);
        IndexBTR index(m_bXP);
        if (index.SearchBTRFile(Path.c_str(), Map, szSearch)) {
          std::vector<std::string> *records = index.GetResults();
          if (records && records->size()) {
            LocationStruct ls;
            std::vector<std::string>::iterator it = records->begin();
            for (; it != records->end(); ++it) {
              if (ParseClassRecordLocation(*it, ls)) {
                InstanceClass *pObject = ParseInstance(*pclassDef, ls);
                if (pObject) {
                  Print(*pObject, logpath, Namespace.c_str(), szClassName);
                  delete pObject;
                }
                break;
              }
              else {
                wprintf_s(L"Parsing the record %s failed.", it->c_str());
                break;
              }
            }
            ret = true;
          }
          else
            ret = true;
        }
        delete pclassDef;
      }
    }
  }
  return ret;
}

bool InstanceDeclarationParser::Parse(const wchar_t* szClassName, const wchar_t *logpath) {
  bool ret = false;
  if (Init()) {
    ClassDefinition *pclassDef = 0;
    ClassDefinitionParser classParser(Path.c_str(), Map, Namespace.c_str());
    if (classParser.Parse(Path.c_str(), szClassName, Map, &pclassDef)) {
      if (pclassDef) {
        std::string szSearch;
        BuildInstanceSearchString(Namespace, szClassName, szSearch, m_bXP);
        IndexBTR index(m_bXP);
        if (index.SearchBTRFile(Path.c_str(), Map, szSearch)) {
          std::vector<std::string> *records = index.GetResults();
          if (records) {
            if (records->size()) {
              LocationStruct ls;
              std::vector<std::string>::iterator it = records->begin();
              for (; it != records->end(); ++it) {
                if (ParseClassRecordLocation(*it, ls)) {
                  InstanceClass *pObject = ParseInstance(*pclassDef, ls);
                  if (pObject) {
                    Print(*pObject, logpath, Namespace.c_str(), szClassName);
                    delete pObject;
                  }
                }
                else {
                  wprintf_s(L"Parsing the record %s failed.", it->c_str());
                  break;
                }
              }
              ret = true;
            }
            else
              ret = true;
          }
        }
        delete pclassDef;
      }
      else
        ret = true;
    }
  }
  return ret;
}

InstanceClass* InstanceDeclarationParser::ParseInstance(ClassDefinition& classDef, LocationStruct &ls) {
  InstanceClass *pObject = 0;
  if (ls.IsValid()) {
    std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
    if (allocMap) {
      std::vector<ExtentClass> recordExtents;
      if (!GetRecordExtents(m_ObjFile, *allocMap, ls, recordExtents))
        return 0;
      BYTE *recBuf = new BYTE[ls.Size];
      if (recBuf) {
        std::vector<ExtentClass>::iterator it = recordExtents.begin();
        DWORD currentIndex = 0;
        DWORD justread = 0;
        for (; it != recordExtents.end(); ++it) {
          LARGE_INTEGER offset;
          offset.QuadPart = it->GetStart();
          if (INVALID_SET_FILE_POINTER != SetFilePointer(m_ObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
            DWORD toRead = static_cast<DWORD>(it->GetCount() & ALL_BITS_32);
            if (::ReadFile(m_ObjFile, recBuf + currentIndex, toRead, &justread, NULL) && toRead == justread) {
              currentIndex += toRead;
            }
            else
              break;
          }
          else
            break;
        }
        pObject = Create(recBuf, recordExtents, ls.Size, classDef, Map.IsXPRepository());
        delete[] recBuf;
      }
    }
  }
  return pObject;
}

void InstanceDeclarationParser::Print(InstanceClass &inst, const wchar_t *logpath, const wchar_t *szNamespace, const wchar_t *szClassname) {
  FILE* pOutFile = CreateLogFile(logpath, L"at, ccs=UNICODE");
  MyPrintFunc(pOutFile, L"Namespace : %s\r\n", szNamespace);
  inst.Print(m_ObjFile, pOutFile);
  if (pOutFile)
    ::fclose(pOutFile);
}

InstanceClass::InstanceClass() {}

InstanceClass::~InstanceClass() {}

void InstanceClass::Print(HANDLE hFile, FILE *out) {
  __super::Print(hFile, out);
  std::vector<InstanceValue>::iterator it = Values.begin();
  MyPrintFunc(out, L"Instance Property:\r\n");
  for (; it != Values.end(); ++it) {
    it->Print(hFile, out);
  }
}

bool InstanceValue::SetDefaultValue(ExtentVectorVectorType& defVal) {
  bool fail = false;
  try{
    if (defVal.size()) {
      Value.reserve(defVal.size());
      std::copy(defVal.begin(), defVal.end(), std::back_inserter(Value));
    }
  }
  catch (...) {
    wprintf(L"InstanceValue::SetDefaultValue failed.\r\n");
    fail = true;
  }
  return !fail;
}

InstanceClass* InstanceDeclarationParser::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, ClassDefinition& classDef, bool bXP) {
  InstanceClass *pObject = 0;
  if (recordBuf && cRecordExtents.size() && size) {
    pObject = new InstanceClass;
    if (pObject) {
      uint32 guidsize = (bXP ? MAX_STRING_XP_COUNT : MAX_STRING_WIN7_COUNT) * sizeof(wchar_t);
      uint64 currentoffset = 0;
      std::vector<ExtentClass> ex;
      CreateFieldExtents(currentoffset, guidsize, cRecordExtents, ex);
      pObject->SetKnownGUID(ex, TS_USTRING);
      currentoffset += guidsize;

      if (currentoffset < size) {
        const BYTE* parseBuf = reinterpret_cast<const BYTE*>(recordBuf);
        if (currentoffset + sizeof(uint64) < size) {
          pObject->SetDate1(*reinterpret_cast<const uint64*>(parseBuf + currentoffset));
          currentoffset += sizeof(uint64);
        }
        else
          goto Exit;
        if (currentoffset + sizeof(uint64) < size) {
          pObject->SetDate2(*reinterpret_cast<const uint64*>(parseBuf + currentoffset));
          currentoffset += sizeof(uint64);
        }
        else
          goto Exit;
        uint32 remainingsize = 0;
        if (currentoffset + sizeof(uint32) < size) {
          remainingsize = *reinterpret_cast<const uint32*>(parseBuf + currentoffset);
          remainingsize &= 0x3FFFFFFF;
          if (currentoffset + remainingsize <= size)
            currentoffset += sizeof(uint32);
          else
            goto Exit;
        }
        else
          goto Exit;
        uint32 classSize = static_cast<uint32>(classDef.GetProps().size());
        uint32 flagBytes = (classSize * 2);
        uint32 datasize = 0;
        flagBytes = (flagBytes / 8) + ((flagBytes % 8) ? 1 : 0);
        if (currentoffset + sizeof(ClassNameStruct) + flagBytes < size) {
          const ClassNameStruct *pclsnameStr = reinterpret_cast<const ClassNameStruct*>(parseBuf + currentoffset);
          currentoffset += sizeof(ClassNameStruct);
          const BYTE *flagsBuf = reinterpret_cast<const BYTE*>(parseBuf + currentoffset);
          currentoffset += flagBytes;
          uint32 tocoffset = currentoffset & ALL_BITS_32;
          const BYTE *toc = reinterpret_cast<const BYTE*>(parseBuf + currentoffset);
          const BYTE *endtoc = toc + classDef.GetSizeOfProps();
          if (currentoffset + classDef.GetSizeOfProps() < size) {
            currentoffset += classDef.GetSizeOfProps();
            uint32 nextSize = *reinterpret_cast<const uint32*>(parseBuf + currentoffset);
            if (currentoffset + nextSize < size) {
              currentoffset += nextSize;
              BYTE nextByteSize = *(parseBuf + currentoffset);
              if (currentoffset + nextByteSize < size) {
                currentoffset += nextByteSize;
                if (currentoffset + sizeof(uint32) < size) {
                  datasize = *reinterpret_cast<const uint32*>(parseBuf + currentoffset);
                  datasize &= 0x3FFFFFFF; // clearing the 2 MSB bits
                  currentoffset += sizeof(uint32);
                  if (currentoffset + datasize <= size) {
                    std::vector<PropertyClass>& props = classDef.GetProps();
                    std::vector<PropertyClass>::iterator it_prop = props.begin();
                    uint32 idx = 0;
                    uint32 dataOffset = currentoffset & ALL_BITS_32;
                    for (; it_prop != props.end(); ++it_prop) {
                      PropertyClass &p = *it_prop;
                      BYTE var = *(flagsBuf + (idx / 4));
                      BYTE flags = (var >> (2 * (idx % 4))) & 0x3;
                      InstanceValue inst_val(p.GetName(), p.GetNameOffset(), p.GetCimType());
                      if (!(flags & PROP_IS_NOT_INITIALIZED)) {
                        bool isarray = false;
                        const QualifierClass::TypeSizes* ptypes = QualifierClass::GetTypeSize(p.GetCimType(), isarray);
                        if (ptypes) {
                          uint32 vsize = ptypes->CimOnDiskSize;
                          if (isarray)
                            vsize = sizeof(uint32);
                          uint32 inclassOff = p.GetOffsetInClass();
                          if (toc + inclassOff + vsize < endtoc) {
                            ExtentVectorType ext;
                            ExtentVectorVectorType vec_Ext;
                            if (flags & PROP_USE_DEFAULT_VALUE) { //use the default value from Class definition
                              inst_val.SetDefaultValue(p.GetDefValue());
                            }
                            else {
                              if (!isarray && ptypes->Inline) {
                                CreateFieldExtents(tocoffset + inclassOff, vsize, cRecordExtents, ext);
                                inst_val.GetValue().push_back(ext);
                              }
                              else {
                                uint32 inDataOffset = *reinterpret_cast<const uint32*>(toc + inclassOff);
                                if (isarray) {
                                  QualifierClass::SetMultiValueExtents(inst_val.GetValue(), cRecordExtents, ptypes, parseBuf, dataOffset, inDataOffset);
                                }
                                else {
                                  uint32 defLen = static_cast<uint32>(strlen(reinterpret_cast<const char*>(parseBuf + dataOffset + inDataOffset + sizeof(BYTE))));
                                  CreateFieldExtents(dataOffset + inDataOffset + sizeof(BYTE), defLen, cRecordExtents, ext);
                                  inst_val.GetValue().push_back(ext);
                                }
                              }
                            }
                          }
                        }
                      }
                      pObject->GetValues().push_back(inst_val);
                      idx++;
                    }
                    return pObject;
                  }
                }
              }
            }
          }
        }
      }
    }
  }
Exit:
  delete pObject;
  return 0;
}

InstanceValue::InstanceValue(StringValue &name, uint32 builtinID, uint32 type) : NameValue(name), BuiltInNameID(), CimType(type) {}

InstanceValue::~InstanceValue() {}

void InstanceValue::Print(HANDLE hFile, FILE *out) {
  MyPrintFunc(out, L"=====================================================================================\r\n");
  MyPrintFunc(out, L"Name: ");
  bool builtin = (BuiltInNameID & QualifierClass::QUALIFIER_BUILTIN) > 0;
  if (builtin) {
    const wchar_t* name = QualifierClass::GetBuiltInName(BuiltInNameID);
    if (name)
      MyPrintFunc(out, L"%s\r\n", name);
    else
      MyPrintFunc(out, L"Unknown Builtin Property Name : 0x%x\r\n", BuiltInNameID);
  }
  else
    NameValue.Print(hFile, out);
  MyPrintFunc(out, L"Type: ");
  MyPrintFunc(out, L"%s(0x%X)\r\n", QualifierClass::GetTypeName(CimType), CimType);
  bool isArray = (CimType & QualifierClass::QUALIFIER_PROP_TYPE_ARRAY) > 0;
  MyPrintFunc(out, L"Array: %s\r\n", (isArray ? L"yes" : L"no"));
  MyPrintFunc(out, L"Value: ");
  if (Value.size()) {
    uint32 t = CimType & (QualifierClass::QUALIFIER_PROP_TYPE_ARRAY - 1);
    std::vector<ExtentVectorType>::iterator it_def_val = Value.begin();
    for (; it_def_val != Value.end(); ++it_def_val) {
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
          if (it_def_val + 1 != Value.end())
            MyPrintFunc(out, L", ");
          else
            MyPrintFunc(out, L"\r\n");
          delete[] val;
        }
      }
    }
  }
  else
    MyPrintFunc(out, L"Not Assigned.\r\n");
  MyPrintFunc(out, L"=====================================================================================\r\n");
}
