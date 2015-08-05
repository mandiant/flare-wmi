#ifndef _DEFINED_HELPER_H
#define _DEFINED_HELPER_H

#include <vector>

#define UNK_5_BYTES 5

#define MAX_STRING_XP_SIZE     0x24
#define MAX_STRING_XP_COUNT    0x20
#define MAX_STRING_WIN7_SIZE   0x44
#define MAX_STRING_WIN7_COUNT  0x40

enum Types {
  TS_BOOLEAN = 0,
  TS_UINT16,
  TS_UINT32,
  TS_UINT64,
  TS_SINT32,
  TS_STRING,
  TS_USTRING,
  TS_BYTEARRAY,
  TS_STRINGARRAY,
  TS_TIME
};

enum ValueTypes {
  VT_UNINT = 0,
  VT_SET
};

struct LocationStruct {
  DWORD LogicalID;
  DWORD RecordID;
  DWORD Size;

  bool IsValid() const {
    return RecordID && Size;
  }
};

struct InstanceStruct {
  char           InstanceID[MAX_STRING_WIN7_SIZE];
  LocationStruct Location;

  bool IsValid() const {
    return Location.IsValid();
  }
};

#pragma pack(1)
struct Toc {
  uint32 RecordID;
  uint32 Offset;
  uint32 Size;
  uint32 Crc32;

  bool IsValid(unsigned int size) const {
    return !IsZero() && Offset && Size && Offset < size && Offset + Size > Offset;
  }

  bool IsZero() const {
    return !(RecordID || Offset || Size || Crc32);
  }

};
#pragma pack()


struct ConsumerDataType {
  int     Type;
  int     Size;
  wchar_t ColumnName[0x80];

};

typedef int(*BinaryCompareFunc)(const void *, const void *);

namespace BinarySearchNS {

  template<class main_type, class search_type> main_type* BinarySearch(std::vector<main_type>& arr, search_type find, BinaryCompareFunc compareFunc, unsigned int *index = 0) {
    int low = 0;
    int high = static_cast<unsigned int>(arr.size() & ALL_BITS_32);
    if (high) {
      --high;

      while (low <= high) {
        int mid = (low + high) / 2;
        main_type *record = arr.data() + mid;
        search_type *member = reinterpret_cast<search_type*>(record);

        if (compareFunc(find, member) < 0)
          high = mid - 1;
        else if (compareFunc(find, member) > 0)
          low = mid + 1;
        else {
          if (index)
            *index = static_cast<unsigned int>(mid);
          return record;
        }
      }
    }
    if (index)
      *index = static_cast<unsigned int>(low);
    return 0;
  }
}

class ExtentClass {
public:
  ExtentClass(uint64 s = 0, uint64 c = 0) : Start(s), Count(c) {}


  ExtentClass(const ExtentClass &copyin)
  {
    Start = copyin.Start;
    Count = copyin.Count;
  }

  ExtentClass& operator=(const ExtentClass &rhs)
  {
    this->Start = rhs.Start;
    this->Count = rhs.Count;
    return *this;
  }

  bool operator==(const ExtentClass &rhs) const
  {
    if (this->Start != rhs.Start) return false;
    if (this->Count != rhs.Count) return false;
    return true;
  }


  uint64 GetStart() const { return Start; }
  uint64 GetCount() const { return Count; }
  void SetStart(uint64 s) { Start = s; }
  void SetCount(uint64 c) { Count = c; }
  void Set(uint64 s, uint64 c) {
    SetStart(s);
    SetCount(c);
  }

private:
  uint64 Start;
  uint64 Count;
};

typedef std::vector<ExtentClass> ExtentVectorType;
typedef std::vector<ExtentVectorType> ExtentVectorVectorType;


class StringValue {
public:
  StringValue() : Type(TS_STRING), ValueType(VT_UNINT) {
  }

  StringValue(uint64 s, uint64 c, int type) : Type(type), ValueType(VT_SET) {
    ExtentClass extent(s, c);
    Extents.push_back(extent);
  }

  StringValue(std::vector<ExtentClass> &e, int type) : Type(type), ValueType(VT_SET) {
    Set(e, type);
  }

  StringValue(const StringValue &copyin) : Type(copyin.Type), ValueType(copyin.ValueType) {
    std::vector<ExtentClass>::const_iterator it = copyin.Extents.cbegin();
    Extents.clear();
    
    for (; it != copyin.Extents.cend(); ++it) {
      Extents.push_back(*it);
    }
  }

  StringValue& operator=(const StringValue &rhs)
  {
    std::vector<ExtentClass>::const_iterator it = rhs.Extents.cbegin();
    Extents.clear();

    for (; it != rhs.Extents.cend(); ++it) {
      Extents.push_back(*it);
    }
    Type = rhs.Type;
    ValueType = rhs.ValueType;
    return *this;
  }

  bool operator==(const StringValue &rhs) const
  {
    if (!(this->Extents.size() == rhs.Extents.size())) return false;

    for (unsigned int i = 0; i < this->Extents.size(); ++i)
      if (!(this->Extents.at(i) == rhs.Extents.at(i)))
        return false;

    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Set(uint64 s, uint64 c, int type) {
    Extents.clear();
    ExtentClass e(s,c);
    Extents.push_back(e);
    ValueType = VT_SET;
    Type = type;
  }

  void Set(std::vector<ExtentClass>& extents, int type) {
    std::vector<ExtentClass>::const_iterator it = extents.cbegin();
    Extents.clear();
    for (; it != extents.cend(); ++it) {
      Extents.push_back(*it);
    }
    ValueType = VT_SET;
    Type = type;
  }

  void Print(HANDLE hFile, FILE* out);
  const wchar_t* GetUnicodeValue(HANDLE hFile);
  const char* GetAniValue(HANDLE hFile);

private:
  std::vector<ExtentClass> Extents;
  int                      Type;
  int                      ValueType;
};

class StringArrayValue {
public:
  StringArrayValue() : Type(TS_STRINGARRAY), ValueType(VT_UNINT) {
  }

  void Add(StringValue &val) {
    ValueType = VT_SET;
    Values.push_back(val);
  }

  void Print(HANDLE hFile, FILE* out);

private:
  std::vector<StringValue> Values;
  int                      Type;
  int                      ValueType;
};

class ByteArrayValue {
public:
  ByteArrayValue() : Type(TS_BYTEARRAY), ValueType(VT_UNINT) {
  }

  ByteArrayValue(uint64 s, uint64 c) : Type(TS_BYTEARRAY), ValueType(VT_UNINT) {
    Set(s, c);
  }

  ByteArrayValue(std::vector<ExtentClass> &e) : Type(TS_BYTEARRAY), ValueType(VT_SET) {
    Set(e);
  }

  ByteArrayValue(const ByteArrayValue &copyin) : Type(copyin.Type), ValueType(copyin.ValueType) {
    std::vector<ExtentClass>::const_iterator it = copyin.Extents.cbegin();
    Extents.clear();

    for (; it != copyin.Extents.cend(); ++it) {
      Extents.push_back(*it);
    }
  }

  bool operator==(const ByteArrayValue &rhs) const
  {
    if (this->Extents.size() != rhs.Extents.size())
      return false;

    for (unsigned int i = 0; i < this->Extents.size(); ++i)
      if (!(this->Extents.at(i) == rhs.Extents.at(i)))
        return false;

    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  ByteArrayValue& operator=(const ByteArrayValue &rhs)
  {
    std::vector<ExtentClass>::const_iterator it = rhs.Extents.cbegin();
    Extents.clear();

    for (; it != rhs.Extents.cend(); ++it) {
      Extents.push_back(*it);
    }
    this->Type = rhs.Type;
    return *this;
  }

  void Set(uint64 s, uint64 c) {
    Extents.push_back(ExtentClass(s, c));
    ValueType = VT_SET;
  }

  void Set(std::vector<ExtentClass>& ex) {
    std::vector<ExtentClass>::const_iterator it = ex.cbegin();
    Extents.clear();

    for (; it != ex.cend(); ++it) {
      Extents.push_back(*it);
    }
    ValueType = VT_SET;
  }

  void Print(HANDLE hFile, FILE* out);

protected:
  std::vector<ExtentClass> Extents;
  int                      Type;
  int                      ValueType;
};

class SidValue : public ByteArrayValue {
public:
  void Print(HANDLE hFile, FILE *out);
};

class BoolValue {
public:
  BoolValue() : Value(false), Type(TS_BOOLEAN), ValueType(VT_SET) {}

  BoolValue(uint16 value) : Type(TS_BOOLEAN), ValueType(VT_UNINT) {
    Set(value);
  }

  BoolValue(const BoolValue &copyin)
  {
    Value = copyin.Value;
    Type = copyin.Type;
    ValueType = copyin.ValueType;
  }

  BoolValue& operator=(const BoolValue &rhs)
  {
    this->Value = rhs.Value;
    this->Type = rhs.Type;
    this->ValueType = rhs.ValueType;
    return *this;
  }

  bool operator==(const BoolValue &rhs) const
  {
    if (this->Value != rhs.Value) return false;
    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Set(uint16 value) {
    if (!value) {
      Value = false;
      ValueType = VT_SET;
    }
    else if (0xFFFF == value) {
      Value = true;
      ValueType = VT_SET;
    }
    else
      ValueType = VT_UNINT;

  }

  void Print(FILE* out);

private:
  bool    Value;
  int     Type;
  int     ValueType;
};

class Uint16Value {
public:
  Uint16Value(uint16 value = 0) : Value(value), Type(TS_UINT32), ValueType(VT_SET) {}

  Uint16Value(const Uint16Value &copyin)
  {
    Value = copyin.Value;
    Type = copyin.Type;
    ValueType = copyin.ValueType;
  }

  Uint16Value& operator=(const Uint16Value &rhs)
  {
    this->Value = rhs.Value;
    this->Type = rhs.Type;
    this->ValueType = rhs.ValueType;
    return *this;
  }

  bool operator==(const Uint16Value &rhs) const
  {
    if (this->Value != rhs.Value) return false;
    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Print(FILE* out);

private:
  uint16  Value;
  int     Type;
  int		ValueType;
};



class Uint32Value {
public:
  Uint32Value(unsigned int value = 0) : Value(value), Type(TS_UINT32), ValueType(VT_SET) {}

  Uint32Value(const Uint32Value &copyin)
  {
    Value = copyin.Value;
    Type = copyin.Type;
    ValueType = copyin.ValueType;
  }

  Uint32Value& operator=(const Uint32Value &rhs)
  {
    this->Value = rhs.Value;
    this->Type = rhs.Type;
    this->ValueType = rhs.ValueType;
    return *this;
  }

  Uint32Value& operator=(uint32 val)
  {
    this->Value = val;
    this->Type = TS_UINT32;
    this->ValueType = VT_SET;
    return *this;
  }

  bool operator==(const Uint32Value &rhs) const
  {
    if (this->Value != rhs.Value) return false;
    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Print(FILE* out);
  uint32 GetValue() { return (VT_SET == ValueType) ? Value : 0; }

private:
  uint32  Value;
  int     Type;
  int		ValueType;
};


class Sint32Value {
public:
  Sint32Value(sint32 value = 0) : Value(value), Type(TS_SINT32), ValueType(VT_SET) {}

  Sint32Value(const Sint32Value &copyin)
  {
    Value = copyin.Value;
    Type = copyin.Type;
    ValueType = copyin.ValueType;
  }

  Sint32Value& operator=(const Sint32Value &rhs)
  {
    this->Value = rhs.Value;
    this->Type = rhs.Type;
    this->ValueType = rhs.ValueType;
    return *this;
  }

  bool operator==(const Sint32Value &rhs) const
  {
    if (this->Value != rhs.Value) return false;
    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Print(FILE* out);

private:
  sint32  Value;
  int     Type;
  int	    ValueType;
};

class Uint64Value {
public:
  Uint64Value(uint64 value = 0) : Value(value), Type(TS_UINT64), ValueType(VT_SET) {}

  Uint64Value(const Uint64Value &copyin)
  {
    Value = copyin.Value;
    Type = copyin.Type;
    ValueType = copyin.ValueType;
  }

  Uint64Value& operator=(const Uint64Value &rhs)
  {
    this->Value = rhs.Value;
    this->Type = rhs.Type;
    this->ValueType = rhs.ValueType;
    return *this;
  }

  Uint64Value& operator=(uint64 val)
  {
    *reinterpret_cast<uint64*>(&this->Value) = val;
    this->Type = TS_UINT64;
    this->ValueType = VT_SET;
    return *this;
  }

  bool operator==(const Uint64Value &rhs) const
  {
    if (this->Value != rhs.Value) return false;
    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Print(FILE* out);

private:
  uint64    Value;
  int       Type;
  int       ValueType;
};

class DateValue {
public:
  DateValue(uint64 value = 0) : Type(TS_TIME), ValueType(VT_SET) {
    *reinterpret_cast<uint64*>(&Value) = value;
  }

  DateValue(const DateValue &copyin)
  {
    Value.dwHighDateTime = copyin.Value.dwHighDateTime;
    Value.dwLowDateTime = copyin.Value.dwLowDateTime;
    Type = copyin.Type;
    ValueType = copyin.ValueType;
  }

  DateValue& operator=(const DateValue &rhs)
  {
    this->Value.dwHighDateTime = rhs.Value.dwHighDateTime;
    this->Value.dwLowDateTime = rhs.Value.dwLowDateTime;
    this->Type = rhs.Type;
    this->ValueType = rhs.ValueType;
    return *this;
  }

  DateValue& operator=(uint64 value)
  {
    *reinterpret_cast<uint64*>(&this->Value) = value;
    this->Type = TS_TIME;
    this->ValueType = VT_SET;
    return *this;
  }

  bool operator==(const DateValue &rhs) const
  {
    if (this->Value.dwHighDateTime != rhs.Value.dwHighDateTime) return false;
    if (this->Value.dwLowDateTime != rhs.Value.dwLowDateTime) return false;
    if (this->Type != rhs.Type) return false;
    if (this->ValueType != rhs.ValueType) return false;
    return true;
  }

  void Print(FILE* out);

private:
  FILETIME  Value;
  int       Type;
  int       ValueType;
};

class ObjectHeaderClass {
public:
  ObjectHeaderClass();
  ObjectHeaderClass(const ObjectHeaderClass &copyin);
  
  virtual ~ObjectHeaderClass();
  virtual void Print(HANDLE hFile, FILE *out);
  
  void SetKnownGUID(uint64 s, uint64 c, int type);
  void SetKnownGUID(std::vector<ExtentClass>& extents, int type);
  void SetDate1(uint64 filetime);
  void SetDate2(uint64 filetime);
  ObjectHeaderClass& operator=(const ObjectHeaderClass &rhs);
  bool operator==(const ObjectHeaderClass &rhs) const;

protected:
  StringValue     KnownGuid;
  DateValue       Date1;
  DateValue       Date2;
};

class ObjectReferenceClass
{
public:
  ObjectReferenceClass();
  ~ObjectReferenceClass();

  static ObjectReferenceClass* Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, LocationStruct &ls, bool bXP);
  static ObjectReferenceClass* Create(const void* recordBuf, std::vector<ExtentClass>& extents, uint32 size, bool bXP);
  StringValue& GetObjectReferredPath() { return ObjectReferredPath; }

private:
  StringValue  Namespace;
  StringValue  ClassName;
  StringValue  PropertyName;
  StringValue  ObjectReferredPath;
};

extern uint64 GetWholeSize(std::vector<ExtentClass> &ex);
extern void PrintBuffer(const void *buffer, unsigned int size, FILE *out);
extern int GetTocSize(const ConsumerDataType* data, int count, int init = 0);
extern void BinToHex(unsigned char *hash, int size, char *szHash);
extern void BinToHex(unsigned char *hash, int size, wchar_t *wszHash);
extern void ToUpper(wchar_t *wszIn);
extern HANDLE InitObjFile(const wchar_t *path);
extern void GetStrId(std::string &strID, std::wstring &strName, bool bXP);
extern void GetWStrId(std::wstring &strID, std::wstring &strName, bool bXP);
extern void CreateFieldExtents(uint64 recoffset, uint64 recsize, std::vector<ExtentClass>& extents, std::vector<ExtentClass>& recextents);
extern int CompareStringIDFunc(const void *s1, const void *s2);
extern bool GetRecordExtents(HANDLE hObjFile, std::vector<DWORD>& allocMap, LocationStruct &ls, std::vector<ExtentClass>& recordExtents);
extern bool ConstructInstanceRecord(std::string &strIn, InstanceStruct &fs);
extern const void* GetBufferFromExtents(HANDLE hFile, std::vector<ExtentClass> &ex, uint32& size);
extern void MyPrintFunc(FILE* pOutFile, const wchar_t *format, ...);
extern FILE * CreateLogFile(const wchar_t* outlog, const wchar_t* perm);
#endif