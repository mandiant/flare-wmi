#include "stdafx.h"
#include "ConsumerParser.h"
#include "Hashing.h"
#include "Helper.h"
#include "indexBTR.h"
#include "EventConsumer.h"
#include "FilterToConsumerBinding.h"

ConsumerParserClass::ConsumerParserClass(MappingFileClass &map) : Map(map), m_bXP(map.IsXPRepository()) {
}

ConsumerParserClass::~ConsumerParserClass(){
  if (m_ObjFile != INVALID_HANDLE_VALUE)
    ::CloseHandle(m_ObjFile);
}

bool ConsumerParserClass::Init(const wchar_t *path) {
  HANDLE hFile = InitObjFile(path);
  if (hFile != INVALID_HANDLE_VALUE) {
    m_ObjFile = hFile;
    return true;
  }
  return false;
}

void ConsumerParserClass::BuildAllInstanceRefSearchString(const wchar_t* szNamespace, const wchar_t* szClass, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\KI_<CLASSNAME>\\IR_*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE2_PREFIX;
  name = szClass;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += REFERENCE_PREFIX;
}

void ConsumerParserClass::BuildInstanceRefSearchString(const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\KI_<CLASSNAME>\\IR_<INSTANCE>\R_ */
  BuildInstanceSearchStringHelper(szNamespace, szType, szInstance, szSearch, bXP);
  szSearch += "\\";
  szSearch += REFERENCE_NAME_PREFIX;
}

void ConsumerParserClass::BuildInstanceRefSearchString(const wchar_t* szNamespace, const wchar_t* szType, std::string&  szInstance, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\KI_<CLASSNAME>\\IR_<INSTANCE>\R_ */
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE2_PREFIX;
  name = szType;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += REFERENCE_PREFIX;
  szSearch += szInstance;
  szSearch += "\\";
  szSearch += REFERENCE_NAME_PREFIX;
}


void ConsumerParserClass::BuildInstanceSearchString(const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_<INSTANCE_NAME>.LogicalPage.RecordID.Size*/
  BuildInstanceSearchStringHelper(szNamespace, szType, szInstance, szSearch, bXP);
  szSearch += ".";
}

void ConsumerParserClass::BuildInstanceSearchStringHelper(const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_<INSTANCE_NAME>*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = szType;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
  name = szInstance;
  GetStrId(strID, name, bXP);
  szSearch += strID;
}

void ConsumerParserClass::BuildAllInstancesSearchString(const wchar_t* szNamespace, std::string& szClass, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  szSearch += szClass;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
}

void ConsumerParserClass::BuildAllInstancesSearchString(const wchar_t* szNamespace, const wchar_t* szType, std::string& szSearch, bool bXP) {
  /*NS_<NAMESPACE>\\CI_<CONSUMER_CLASS>\\IL_*/
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_PREFIX;
  name = szType;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += INSTANCE_NAME_PREFIX;
}

void ConsumerParserClass::BuildConsumerClassSearchString(const wchar_t* szNamespace,  std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\\CR_<__EventConsumer>\C_
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_PREFIX;
  name = CONSUMER_BASE_CLASS;
  GetStrId(strID, name, bXP);
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_SUB_PREFIX;
}

void ConsumerParserClass::BuildConsumerClassDefSearchString(const wchar_t* szNamespace, std::string& szClass, std::string& szSearch, bool bXP) {
  //NS_<NAMESPACE>\CD_<Instance>.LogicalPage.RecordID.Size
  std::string strID;
  std::wstring name(szNamespace);
  GetStrId(strID, name, bXP);
  szSearch = NAMESPACE_PREFIX;
  szSearch += strID;
  szSearch += "\\";
  szSearch += CLASS_DEF_PREFIX;
  szSearch += szClass;
}


bool ConsumerParserClass::GetNewConsumerClass(std::string& strIn, const wchar_t* szNamespace, std::string& szConsumerClass, bool bXP) {
  std::string szSearch;
  bool ret = false;
  BuildConsumerClassSearchString(szNamespace, szSearch, bXP);
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      char* found = strstr(szIn, szSearch.c_str());
      if (found) {
        szConsumerClass = found + szSearch.size();
        ret = true;
      }
    }
    delete [] szIn;
  }
  return ret;
}

bool ConsumerParserClass::ParseAllConsumers(const wchar_t* path, const wchar_t* szNamespace) {
  if (Init(path) && szNamespace) {
    IndexBTR index(m_bXP);
    std::string szSearch;
    BuildConsumerClassSearchString(szNamespace, szSearch, m_bXP);
    if (index.SearchBTRFile(path, Map, szSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records) {
        std::vector<std::string>::iterator it = records->begin();
        std::vector<std::string> aConsumerClasses;
        for (; it != records->end(); ++it) {
          std::string szClass;
          if (GetNewConsumerClass(*it, szNamespace, szClass, m_bXP)) {
            std::string szInstSearch;
            BuildAllInstancesSearchString(szNamespace, szClass, szInstSearch, m_bXP);
            aConsumerClasses.push_back(szInstSearch);
          }
        }
        if (aConsumerClasses.size()) {
          std::vector<std::string>::iterator it = aConsumerClasses.begin();
          for (; it != aConsumerClasses.end(); ++it) {
            if (index.SearchBTRFile(path, Map, *it)) {
              std::vector<std::string> *records = index.GetResults();
              if (records) {
                std::vector<std::string>::iterator it = records->begin();
                for (; it != records->end(); ++it) {
                  InstanceStruct cs;
                  ::memset(&cs, 0, sizeof(InstanceStruct));
                  if (ConstructInstanceRecord(*it, cs))
                    AddConsumer(cs);
                }
              }
            }
          }
        }
        return true;
      }
    }
  }
  return false;
}

bool ConsumerParserClass::ParseAllConsumersByType(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType) {
  if (Init(path) && szNamespace && szType) {
    IndexBTR index(m_bXP);
    std::string szSearch;
    BuildAllInstancesSearchString(szNamespace, szType, szSearch, m_bXP);
    if (index.SearchBTRFile(path, Map, szSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records) {
        std::vector<std::string>::iterator it = records->begin();
        for (; it != records->end(); ++it) {
          InstanceStruct cs;
          ::memset(&cs, 0, sizeof(InstanceStruct));
          if (ConstructConsumerRecord(*it, szNamespace, szType, cs))
            AddConsumer(cs);
        }
        return true;
      }
    }
  }
  return false;
}

bool ConsumerParserClass::ParseConsumerInstance(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstanceName) {
  if (Init(path) && szNamespace && szType) {
    IndexBTR index(m_bXP);
    std::string szSearch;
    BuildInstanceSearchString(szNamespace, szType, szInstanceName, szSearch, m_bXP);
    if (index.SearchBTRFile(path, Map, szSearch)) {
      std::vector<std::string> *records = index.GetResults();
      if (records && records->size()) {
        InstanceStruct cs;
        ::memset(&cs, 0, sizeof(InstanceStruct));
        if (ConstructInstanceRecord(records->at(0), cs)) {
          AddConsumer(cs);
          return true;
        }
      }
    }
  }
  return false;
}

InstanceStruct* ConsumerParserClass::FindConsumer(std::string &str, const wchar_t* szNamespace, const wchar_t* szType) {
  std::string strSearch;
  BuildAllInstanceRefSearchString(szNamespace, szType, strSearch, m_bXP);
  if (!str.find(strSearch)) {
    int count = m_bXP ? MAX_STRING_XP_COUNT : MAX_STRING_WIN7_COUNT;
    if (str.length() > strSearch.length() + count) {
      char * instID = new char[count + 1];
      if (instID) {
        if (!strncpy_s(instID, count + 1, str.c_str() + strSearch.length(), count))
          return BinarySearchNS::BinarySearch<InstanceStruct, const char*>(Consumers, instID, CompareStringIDFunc);
      }
    }
  }
  return 0;
}

void ConsumerParserClass::AddConsumer(InstanceStruct& cs) {
  unsigned int index = 0;
  InstanceStruct* foundStruct = BinarySearchNS::BinarySearch<InstanceStruct, const char*>(Consumers, cs.InstanceID, CompareStringIDFunc, &index);
  if (!foundStruct) {
    std::vector<InstanceStruct>::iterator it = Consumers.begin();
    std::advance(it, index);
    Consumers.insert(it, cs);
  }
}


bool ConsumerParserClass::GetConsumerBinding(const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType, std::vector<DWORD>& allocMap, InstanceStruct& cs, std::vector<InstanceStruct> &bindings) {
  std::vector<BindingStruct>  bindingRefs;
  std::string strInstanceName(cs.InstanceID);
  std::string strSearch;
  BuildInstanceRefSearchString(szNamespace, szType, strInstanceName, strSearch, m_bXP);
  IndexBTR index(m_bXP);
  std::vector<std::string> bindingArray;
  if (index.SearchBTRFile(path, Map, strSearch)) {
    std::vector<std::string> *records = index.GetResults();
    if (records) {
      if (!records->size())
        return true;
      std::vector<std::string>::iterator it = records->begin();
      ObjectReferenceClass *ref = 0;
      BindingStruct bs;
      for (; it != records->end(); ++it) {
        ::memset(&bs, 0, sizeof(BindingStruct));
        if (!ParseBinding(bs, *it, strSearch))
          break;
        if (!SUCCEEDED(StringCbCopyA(bs.InstanceID, sizeof(bs.InstanceID), cs.InstanceID)))
          break;
        ref = ObjectReferenceClass::Create(m_ObjFile, allocMap, bs.Binding.Location, m_bXP);
        if (!ref)
          break;
        const char *bindingpath = ref->GetObjectReferredPath().GetAniValue(m_ObjFile);
        if (bindingpath && *bindingpath) {
          std::string strBinding(bindingpath);
          bindingArray.push_back(strBinding);
          delete[] bindingpath;
        }
        delete ref;
      }
    }
  }
  if (bindingArray.size()) {
    std::vector<std::string>::iterator it = bindingArray.begin();
    for (; it != bindingArray.end(); ++it) {
      index.ResetResults();
      if (index.SearchBTRFile(path, Map, *it)) {
        std::vector<std::string> *records = index.GetResults();
        if (records && records->size() == 1) {
          InstanceStruct binds;
          if (ConstructInstanceRecord(records->at(0), binds))
            bindings.push_back(binds);
        }
      }
    }
    return true;
  }
  return false;
}

bool ConsumerParserClass::ParseBinding(BindingStruct &bs, std::string &strIn, std::string &str) {
  bool ret = false;
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      char* found = strstr(szIn, str.c_str());
      if (found) {
        char* strInstance = found + str.size();
        int index = 0;
        while (index < 3) {
          char *szDot = strrchr(strInstance, '.');
          if (!szDot)
            goto Exit;
          char *val = szDot + 1;
          *szDot = 0;
          if (!index)
            bs.Binding.Location.Size = atoll(val) & ALL_BITS_32;
          else if (1 == index)
            bs.Binding.Location.RecordID = atoll(val) & ALL_BITS_32;
          else {
            bs.Binding.Location.LogicalID = atoll(val) & ALL_BITS_32;
            if (!SUCCEEDED(StringCbCopyA(bs.Binding.InstanceID, sizeof(bs.Binding.InstanceID), strInstance)))
              goto Exit;
          }
          index++;
        }
        ret = true;
      }
    }
  Exit:
    delete[] szIn;
  }
  return ret;
}

bool ConsumerParserClass::ConstructConsumerRecord(std::string &strIn, const wchar_t* szNamespace, const wchar_t* szType, InstanceStruct& cs) {
  bool ret = false;
  std::string str;
  BuildAllInstancesSearchString(szNamespace, szType, str, m_bXP);
  if (char * szIn = new char[strIn.length() + 1]) {
    if (!strcpy_s(szIn, strIn.length() + 1, strIn.c_str())) {
      char* found = strstr(szIn, str.c_str());
      if (found) {
        char* strInstance = found + str.size();
        int index = 0;
        while (index < 3) {
          char *szDot = strrchr(strInstance, '.');
          if (!szDot)
            goto Exit;
          char *val = szDot + 1;
          *szDot = 0;
          if (!index)
            cs.Location.Size = atoll(val) & ALL_BITS_32;
          else if (1 == index)
            cs.Location.RecordID = atoll(val) & ALL_BITS_32;
          else {
            cs.Location.LogicalID = atoll(val) & ALL_BITS_32;
            if (!SUCCEEDED(StringCbCopyA(cs.InstanceID, sizeof(cs.InstanceID), strInstance)))
              goto Exit;
          }
          index++;
        }
        ret = true;
      }
    }
    Exit:
    delete[] szIn;
  }
  return ret;
}

void ConsumerParserClass::Print(const wchar_t* outlog, const wchar_t* szNamespace, const wchar_t* szType) {
  FILE* out = CreateLogFile(outlog, L"at, ccs=UNICODE");
  std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
  if (allocMap) {
    if (szType)
      MyPrintFunc(out, L"==== %s in namespace %s ====\n", szType, szNamespace);
    else
      MyPrintFunc(out, L"==== Consumers in namespace %s ====\n", szNamespace);
    std::vector<InstanceStruct>::iterator it = Consumers.begin();
    for (; it != Consumers.end(); ++it) {
      MyPrintFunc(out, L"[%S]:\nConsumer:(%.8X.%.8X.%.8X)\n", it->InstanceID, it->Location.LogicalID, it->Location.RecordID, it->Location.Size);
      EventConsumer* p = EventConsumer::Create(m_ObjFile, *allocMap, *it, szType, m_bXP);
      if (p) {
        p->Print(m_ObjFile, out);
        delete p;
      }
    }
    MyPrintFunc(out, L"=============================================================================\n");
    if (out)
      ::fclose(out);
  }
}

void ConsumerParserClass::Print(const wchar_t* outlog, const wchar_t* path, const wchar_t* szNamespace, const wchar_t* szType, const wchar_t* szInstance) {
  FILE* out = CreateLogFile(outlog, L"at, ccs=UNICODE");
  std::vector<DWORD> *allocMap = Map.GetDataAllocMap();
  if (allocMap) {
    MyPrintFunc(out, L"==== %s\\%s\\%s====\n", szNamespace, szType, szInstance);
    std::vector<InstanceStruct>::iterator it = Consumers.begin();
    for (; it != Consumers.end(); ++it) {
      MyPrintFunc(out, L"[%S]:\nConsumer:(%.8X.%.8X.%.8X)\n", it->InstanceID, it->Location.LogicalID, it->Location.RecordID, it->Location.Size);
      EventConsumer* p = EventConsumer::Create(m_ObjFile, *allocMap, *it, szType, m_bXP);
      if (p) {
        p->Print(m_ObjFile, out);
        delete p;
        if (szType && szInstance) {
          std::vector<InstanceStruct> bindings;
          if (GetConsumerBinding(path, szNamespace, szType, *allocMap, *it, bindings)) {
            std::vector<InstanceStruct>::iterator bindit = bindings.begin();
            for (; bindit != bindings.end(); ++bindit) {
              MyPrintFunc(out, L"[%S]:\nBinding:(%.8X.%.8X.%.8X)\n", bindit->InstanceID, bindit->Location.LogicalID, bindit->Location.RecordID, bindit->Location.Size);
              FilterToConsumerBindingClass*b = FilterToConsumerBindingClass::Create(m_ObjFile, *allocMap, *bindit, m_bXP);
              if (b) {
                b->Print(m_ObjFile, out);
                delete b;
              }
            }
          }
        }
      }
    }
    MyPrintFunc(out, L"=============================================================================\n");
    if (out)
      ::fclose(out);
  }
}
